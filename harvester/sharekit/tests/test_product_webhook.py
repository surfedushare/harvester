from django.test import override_settings
from django.urls import reverse
from django.utils.timezone import now

from sharekit.tests.factories import SharekitMetadataHarvestFactory
from testing.cases.webhooks import product as product_test_case
from testing.utils.factories import create_datatype_models


WEBHOOKS = {
    "sharekit:edusources": {
        "secret": product_test_case.TEST_WEBHOOK_SECRET,
        "allowed_ips": [product_test_case.TEST_WEBHOOK_IP]
    }
}


@override_settings(WEBHOOKS=WEBHOOKS)
class TestSharekitProductWebhook(product_test_case.TestProductWebhookTestCase):

    entity_type = "products"
    product_seeds = None
    file_seeds = None

    @classmethod
    def load_product_test_data(cls):
        cls.set_names = ["sharekit:edusources"]
        cls.product_seeds = [
            {
                "state": "active",
                "set": "sharekit:edusources",
                "external_id": "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257",
                "title": "Should become 'Using a Vortex (responsibly) | Wageningen UR'",
                "language": "en"
            },
            {
                "state": "active",
                "set": "sharekit:edusources",
                "external_id": "63903863-6c93-4bda-b850-277f3c9ec00e",
                "title": "To be deleted",
                "language": "nl"
            }
        ]
        cls.file_seeds = [
            {
                "state": "active",
                "set": "sharekit:edusources",
                "external_id": "0ed38cdc914e5e8a6aa1248438a1e2032a14b0de",
                "url": "https://surfsharekit.nl/objectstore/182216be-31a2-43c3-b7de-e5dd355b09f7",
                "product_id": "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257",
            },
            {
                "state": "active",
                "set": "sharekit:edusources",
                "external_id": "8b714937aab9bda1005d8aa76c607e629b25d89e",
                "url": "https://www.youtube.com/watch?v=Zl59P5ZNX3M",
                "product_id": "63903863-6c93-4bda-b850-277f3c9ec00e",
            }
        ]
        cls.product_dataset, cls.product_dataset_version, cls.product_sets, cls.product_documents = (
            create_datatype_models("products", cls.set_names, cls.product_seeds, 2)
        )
        cls.files_dataset, cls.files_dataset_version, cls.files_sets, cls.files_documents = (
            create_datatype_models("files", cls.set_names, cls.file_seeds, 2)
        )

    @classmethod
    def load_sharekit_test_data(cls):
        # Load the data that we'll be sending to the webhook view
        delta_response = SharekitMetadataHarvestFactory.create(is_initial=False, number=0)
        content_type, delta = delta_response.content
        delta_records = delta["data"]
        return {
            "create": delta_records[2],
            "update": delta_records[0],
            "delete": delta_records[1]
        }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.load_product_test_data()
        cls.test_start_time = now()
        cls.webhook_url = reverse("product-webhook", args=("sharekit", "edusources", cls.webhook_secret,))
        cls.test_data = cls.load_sharekit_test_data()
        cls.data_key = "attributes"
