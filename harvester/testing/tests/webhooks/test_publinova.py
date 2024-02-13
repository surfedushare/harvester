from django.test import override_settings
from django.urls import reverse
from django.utils.timezone import now

from sources.factories.publinova.extraction import PublinovaMetadataResourceFactory
from testing.cases.webhooks import product as product_test_case
from testing.utils.factories import create_datatype_models


WEBHOOKS = {
    "publinova:publinova": {
        "secret": product_test_case.TEST_WEBHOOK_SECRET,
        "allowed_ips": [product_test_case.TEST_WEBHOOK_IP]
    }
}


@override_settings(WEBHOOKS=WEBHOOKS)
class TestPublinovaProductWebhook(product_test_case.TestProductWebhookTestCase):

    entity_type = "products"
    product_seeds = None
    file_seeds = None
    product_documents = []

    @classmethod
    def load_product_test_data(cls):
        cls.set_names = ["publinova:publinova"]
        cls.product_seeds = [
            {
                "state": "active",
                "set": "publinova:publinova",
                "external_id": "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257",
                "title": "Should become 'Using a Vortex (responsibly) | Wageningen UR'",
                "language": "unk",
            },
            {
                "state": "active",
                "set": "publinova:publinova",
                "external_id": "63903863-6c93-4bda-b850-277f3c9ec00e",
                "title": "To be deleted",
                "language": "unk",
            }
        ]
        cls.file_seeds = [
            {
                "state": "active",
                "set": "publinova:publinova",
                "external_id": "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257:b1e07b1c3e68ae63abf8da023169609d50266a01",
                "url": "https://api.publinova.acc.surf.zooma.cloud/api/products/0b8efc72-a7a8-4635-9de9-84010e996b9e/"
                       "download/41ab630b-fce0-431a-a523-078ca000c1c4",
                "product_id": "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257",
            },
            {
                "state": "active",
                "set": "publinova:publinova",
                "external_id": "63903863-6c93-4bda-b850-277f3c9ec00e:0ed38cdc914e5e8a6aa1248438a1e2032a14b0de",
                "url": "https://surfsharekit.nl/objectstore/182216be-31a2-43c3-b7de-e5dd355b09f7",
                "product_id": "63903863-6c93-4bda-b850-277f3c9ec00e",
            },
        ]
        cls.product_dataset, cls.product_dataset_version, cls.product_sets, cls.product_documents = (
            create_datatype_models("products", cls.set_names, cls.product_seeds, 2)
        )
        cls.files_dataset, cls.files_dataset_version, cls.files_sets, cls.files_documents = (
            create_datatype_models("files", cls.set_names, cls.file_seeds, 2)
        )
        cls.update_document = cls.product_documents[0]

    @classmethod
    def load_publinova_test_data(cls):
        delta_response = PublinovaMetadataResourceFactory.create(is_initial=True, number=0)
        content_type, delta = delta_response.content
        delta_records = delta["data"]
        cls.test_data = {
            "create": delta_records[2],
            "update": delta_records[0],
            "delete": {
                "id": "63903863-6c93-4bda-b850-277f3c9ec00e",
                "state": "deleted"
            }
        }
        cls.test_product_ids = {
            test_type: product_data["id"]
            for test_type, product_data in cls.test_data.items()
        }

    @classmethod
    def setUpTestData(cls):
        cls.load_product_test_data()
        cls.test_start_time = now()
        cls.webhook_url = reverse("product-webhook", args=("publinova", "publinova", cls.webhook_secret,))
        cls.load_publinova_test_data()
