import json
from copy import deepcopy

from django.test import TestCase, override_settings

from core.loading import load_harvest_models


TEST_WEBHOOK_SECRET = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TEST_WEBHOOK_IP = "20.56.15.206"
WEBHOOKS = {
   "sharekit:edusources": {
       "secret": TEST_WEBHOOK_SECRET,
       "allowed_ips": [TEST_WEBHOOK_IP]
   }
}


@override_settings(WEBHOOKS=WEBHOOKS)
class TestProductWebhookTestCase(TestCase):

    webhook_secret = TEST_WEBHOOK_SECRET
    test_ip = TEST_WEBHOOK_IP
    test_start_time = None
    webhook_url = None
    data_key = None
    test_data = None
    entity_type = None
    set_names = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        models = load_harvest_models(cls.entity_type)
        cls.Document = models["Document"]

    def call_webhook(self, url, ip=None, verb="create", overrides=None):
        data = deepcopy(self.test_data[verb])
        if isinstance(overrides, dict):
            if self.data_key is not None:
                data[self.data_key].update(overrides)
            else:
                data.update(overrides)
        return self.client.post(
            url,
            data=data,
            content_type="application/vnd.api+json",
            HTTP_X_FORWARDED_FOR=ip or self.test_ip
        )

    def test_invalid_secret(self):
        no_uuid_secret_url = self.webhook_url.replace(self.webhook_secret, "invalid")
        no_uuid_response = self.call_webhook(no_uuid_secret_url)
        self.assertEqual(no_uuid_response.status_code, 404)
        invalid_secret = self.webhook_secret.replace(self.webhook_secret[:8], "b" * 8)
        invalid_secret_url = self.webhook_url.replace(self.webhook_secret, invalid_secret)
        invalid_secret_response = self.call_webhook(invalid_secret_url)
        self.assertEqual(invalid_secret_response.status_code, 403)
        self.assertEqual(invalid_secret_response.reason_phrase, "Webhook not allowed in this environment")

    def test_invalid_ip(self):
        invalid_ip_response = self.call_webhook(self.webhook_url, ip="127.6.6.6")
        self.assertEqual(invalid_ip_response.status_code, 403)
        self.assertEqual(invalid_ip_response.reason_phrase, "Webhook not allowed from source")

    def test_invalid_data(self):
        encoded_data = json.dumps(self.test_data["create"])
        invalid_data_response = self.client.post(
            self.webhook_url,
            data=encoded_data[:10],  # an arbitrarily chosen mutilation of the JSON
            content_type="text/html",
            HTTP_X_FORWARDED_FOR=self.test_ip
        )
        self.assertEqual(invalid_data_response.status_code, 400)
        self.assertEqual(invalid_data_response.reason_phrase, "Invalid JSON")

    def test_create(self):
        self.assertIsNone(
            self.Document.objects.filter(properties__external_id="3e45b9e3-ba76-4200-a927-2902177f1f6c").last(),
            "Document with external_id 3e45b9e3-ba76-4200-a927-2902177f1f6c should not exist before the test"
        )
        create_response = self.call_webhook(self.webhook_url)
        self.assertEqual(create_response.status_code, 200)
        create_document = self.Document.objects \
            .filter(properties__external_id="3e45b9e3-ba76-4200-a927-2902177f1f6c") \
            .last()
        self.assertIsNotNone(create_document)
        self.assertGreater(create_document.created_at, self.test_start_time)
        self.assertGreater(create_document.modified_at, self.test_start_time)

    def test_update(self):
        update_response = self.call_webhook(self.webhook_url, verb="update")
        self.assertEqual(update_response.status_code, 200)
        update_document = self.Document.objects \
            .filter(properties__external_id="5be6dfeb-b9ad-41a8-b4f5-94b9438e4257") \
            .last()
        self.assertIsNotNone(update_document)
        self.assertLess(update_document.created_at, self.test_start_time)
        self.assertGreater(update_document.modified_at, self.test_start_time)
        self.assertEqual(update_document.properties["title"], "Using a Vortex (responsibly) | Wageningen UR")

    def test_delete(self):
        delete_response = self.call_webhook(self.webhook_url, verb="delete")
        self.assertEqual(delete_response.status_code, 200)
        delete_document = self.Document.objects \
            .filter(properties__external_id="63903863-6c93-4bda-b850-277f3c9ec00e") \
            .last()
        self.assertIsNotNone(delete_document)
        self.assertLess(delete_document.created_at, self.test_start_time)
        self.assertGreater(delete_document.modified_at, self.test_start_time)
        self.assertEqual(delete_document.properties["state"], "deleted")

    def test_create_no_language(self):
        self.assertIsNone(
            self.Document.objects.filter(properties__external_id="3e45b9e3-ba76-4200-a927-2902177f1f6c").last(),
            "Document with external_id 3e45b9e3-ba76-4200-a927-2902177f1f6c should not exist before the test"
        )
        create_response = self.call_webhook(self.webhook_url, overrides={"language": None})
        self.assertEqual(create_response.status_code, 200)
        create_document = self.Document.objects \
            .filter(properties__external_id="3e45b9e3-ba76-4200-a927-2902177f1f6c") \
            .last()
        self.assertIsNotNone(create_document)
        self.assertGreater(create_document.created_at, self.test_start_time)
        self.assertGreater(create_document.modified_at, self.test_start_time)
        self.assertEqual(
            create_document.get_language(), "unk",
            "Expected language to become 'unk' if source indicates None"
        )

    def test_update_no_language(self):
        update_response = self.call_webhook(self.webhook_url, verb="update", overrides={"language": None})
        self.assertEqual(update_response.status_code, 200)
        update_document = self.Document.objects \
            .filter(properties__external_id="5be6dfeb-b9ad-41a8-b4f5-94b9438e4257") \
            .last()
        self.assertIsNotNone(update_document)
        self.assertLess(update_document.created_at, self.test_start_time)
        self.assertGreater(update_document.modified_at, self.test_start_time)
        self.assertEqual(update_document.properties["title"], "Using a Vortex (responsibly) | Wageningen UR")
        self.assertEqual(update_document.get_language(), "en", "Expected language to never change")

    def test_tasks_reset(self):
        self.skipTest("Test should assert that setting certain properties will re-run tasks")
