import json
from copy import deepcopy
from unittest.mock import patch, call

from django.test import TestCase, override_settings

from core.loading import load_harvest_models
from products.models import ProductDocument
from files.models import FileDocument


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
    test_data = {}
    test_product_ids = {}
    entity_type = None
    set_names = None

    update_document = None

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

    def assert_create_models_dont_exist(self):
        create_id = self.test_product_ids["create"]
        self.assertIsNone(
            ProductDocument.objects.filter(identity=create_id).last(),
            f"ProductDocument with external_id {create_id} should not exist before the test"
        )

    def reload_document_models(self, test_type):
        product_id = self.test_product_ids[test_type]
        product_document = ProductDocument.objects.filter(properties__external_id=product_id).last()
        file_document = FileDocument.objects.filter(properties__product_id=product_id).last()
        return product_document, file_document

    def assert_create_models(self):
        create_product, create_file = self.reload_document_models("create")
        # Product asserts
        self.assertIsNotNone(create_product)
        self.assertEqual(create_product.state, "active")
        self.assertGreater(create_product.created_at, self.test_start_time)
        self.assertGreater(create_product.modified_at, self.test_start_time)
        # File asserts
        self.assertIsNotNone(create_file)
        self.assertEqual(create_file.state, "active")
        self.assertGreater(create_file.created_at, self.test_start_time)
        self.assertGreater(create_file.modified_at, self.test_start_time)
        return create_product, create_file

    def assert_update_models(self):
        update_product, update_file = self.reload_document_models("update")
        # Product asserts
        self.assertIsNotNone(update_product)
        self.assertEqual(update_product.state, "active")
        self.assertLess(update_product.created_at, self.test_start_time)
        self.assertGreater(update_product.modified_at, self.test_start_time)
        self.assertEqual(update_product.properties["title"], "Using a Vortex (responsibly) | Wageningen UR")
        # Check that applied-science gets replaced and will re-trigger task
        self.assertEqual(
            update_product.properties["learning_material"]["study_vocabulary"],
            ["http://purl.edustandaard.nl/concept/7aae4604-bdf4-40ab-81e9-673c697595f9"],
            "Expected applied-science term to be replaced with id for 'DNA Sequencing'"
        )
        self.assertIsNotNone(update_product.pending_at)
        self.assertIsNone(update_product.finished_at)
        self.assertEqual(
            update_product.pipeline, {},
            "Expected tasks to get reset because of new study_vocabulary term"
        )
        # File asserts
        self.assertIsNotNone(update_file)
        self.assertEqual(update_file.state, "active")
        self.assertLess(update_file.created_at, self.test_start_time)
        self.assertGreater(update_file.modified_at, self.test_start_time)
        return update_product, update_file

    def assert_delete_models(self):
        delete_product, delete_file = self.reload_document_models("delete")
        # Product asserts
        self.assertIsNotNone(delete_product)
        self.assertEqual(delete_product.state, "deleted")
        self.assertLess(delete_product.created_at, self.test_start_time)
        self.assertGreater(delete_product.modified_at, self.test_start_time)
        self.assertEqual(delete_product.properties["state"], "deleted")
        self.assertEqual(delete_product.properties["title"], "To be deleted",
                         "Expected properties of deleted products to remain intact")
        self.assertEqual(delete_product.pipeline, {"lookup_study_vocabulary_parents": {"success": True}},
                         "Expected tasks to remain valid after deletion")
        # File asserts
        self.assertIsNotNone(delete_file)
        self.assertEqual(delete_product.state, "deleted")
        self.assertLess(delete_file.created_at, self.test_start_time)
        self.assertGreater(delete_file.modified_at, self.test_start_time)
        self.assertEqual(delete_file.properties["state"], "deleted")
        return delete_product, delete_file

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

    @patch("products.views.webhook.dispatch_document_tasks.delay")
    def test_create(self, dispatch_mock):
        self.assert_create_models_dont_exist()
        create_response = self.call_webhook(self.webhook_url)
        self.assertEqual(create_response.status_code, 200)
        create_product, create_file = self.assert_create_models()
        # Dispatch asserts
        dispatch_mock.assert_has_calls([
            call("products", [create_product.id]),
            call("files", [create_file.id])
        ])

    @patch("products.views.webhook.dispatch_document_tasks.delay")
    def test_update(self, dispatch_mock):
        update_response = self.call_webhook(self.webhook_url, verb="update")
        self.assertEqual(update_response.status_code, 200)
        update_product, update_file = self.assert_update_models()
        # Dispatch asserts
        dispatch_mock.assert_has_calls([
            call("products", [update_product.id]),
            call("files", [update_file.id])
        ])

    @patch("products.views.webhook.dispatch_document_tasks.delay")
    def test_delete(self, dispatch_mock):
        delete_response = self.call_webhook(self.webhook_url, verb="delete")
        self.assertEqual(delete_response.status_code, 200)
        self.assert_delete_models()
        # Dispatch asserts
        dispatch_mock.assert_has_calls([
            call("products", []),
            call("files", [])
        ])

    @patch("products.views.webhook.dispatch_document_tasks.delay")
    def test_create_no_language(self, dispatch_mock):
        self.assert_create_models_dont_exist()
        create_response = self.call_webhook(self.webhook_url, overrides={"language": None})
        self.assertEqual(create_response.status_code, 200)
        create_product, create_file = self.assert_create_models()
        # Dispatch asserts
        dispatch_mock.assert_has_calls([
            call("products", [create_product.id]),
            call("files", [create_file.id])
        ])

    @patch("products.views.webhook.dispatch_document_tasks.delay")
    def test_update_no_language(self, dispatch_mock):
        update_response = self.call_webhook(self.webhook_url, verb="update", overrides={"language": None})
        self.assertEqual(update_response.status_code, 200)
        update_product, update_file = self.assert_update_models()
        # Dispatch asserts
        dispatch_mock.assert_has_calls([
            call("products", [update_product.id]),
            call("files", [update_file.id])
        ])

    @patch("products.views.webhook.dispatch_document_tasks.delay")
    def test_update_deleted(self, dispatch_mock):
        # Prepare update Document
        self.update_document.state = ProductDocument.States.DELETED
        self.update_document.properties["state"] = ProductDocument.States.DELETED
        self.update_document.save()
        # Execute the webhook
        update_response = self.call_webhook(self.webhook_url, verb="update")
        self.assertEqual(update_response.status_code, 200)
        update_product, update_file = self.assert_update_models()
        # Dispatch asserts
        dispatch_mock.assert_has_calls([
            call("products", [update_product.id]),
            call("files", [update_file.id])
        ])
