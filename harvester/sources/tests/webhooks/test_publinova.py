from django.test import override_settings
from django.urls import reverse
from django.utils.timezone import now

from core.models import Collection
from sources.factories.publinova.extraction import PublinovaMetadataResourceFactory
from testing.cases.webhooks import legacy as webhook_test_base


WEBHOOKS = {
    "publinova": {
        "secret": webhook_test_base.TEST_WEBHOOK_SECRET,
        "allowed_ips": [webhook_test_base.TEST_WEBHOOK_IP]
    }
}


@override_settings(WEBHOOKS=WEBHOOKS)
class TestPublinovaDocumentWebhook(webhook_test_base.TestEditDocumentWebhook):

    fixtures = ["datasets-history"]

    @classmethod
    def load_publinova_test_data(cls):
        delta_response = PublinovaMetadataResourceFactory.create(is_initial=True, number=0)
        content_type, delta = delta_response.content
        delta_records = delta["data"]
        return {
            "create": delta_records[2],
            "update": delta_records[0],
            "delete": {
                "id": "63903863-6c93-4bda-b850-277f3c9ec00e",
                "state": "deleted"
            }
        }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Collection.objects.filter(name="edusources").update(name="publinova")
        cls.test_start_time = now()
        cls.webhook_url = reverse("publinova-document-webhook", args=("publinova", cls.webhook_secret,))
        cls.test_data = cls.load_publinova_test_data()
