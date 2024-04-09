from django.test import override_settings
from django.urls import reverse
from django.utils.timezone import now

from sharekit.tests.factories import SharekitMetadataHarvestFactory
from testing.cases.webhooks import legacy as webhook_test_base


WEBHOOKS = {
    "edusources": {
        "secret": webhook_test_base.TEST_WEBHOOK_SECRET,
        "allowed_ips": [webhook_test_base.TEST_WEBHOOK_IP]
    }
}


@override_settings(WEBHOOKS=WEBHOOKS)
class TestSharekitDocumentWebhook(webhook_test_base.TestEditDocumentWebhook):

    fixtures = ["datasets-history"]

    @classmethod
    def load_sharekit_test_data(cls):
        delta_response = SharekitMetadataHarvestFactory.create(is_initial=False, number=0)
        content_type, delta = delta_response.content
        delta_records = delta["data"]
        return {
            "create": delta_records[2],
            "update": delta_records[1],
            "delete": delta_records[0]
        }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_start_time = now()
        cls.webhook_url = reverse("sharekit-document-webhook", args=("edusources", cls.webhook_secret,))
        cls.test_data = cls.load_sharekit_test_data()
        cls.data_key = "attributes"
