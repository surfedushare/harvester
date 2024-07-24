from django.test import override_settings
from django.urls import reverse
from django.utils.timezone import now

from sources.factories.sharekit.extraction import SharekitMetadataHarvestFactory
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
    product_documents = []
    support_study_vocabulary = True

    @classmethod
    def load_product_test_data(cls):
        cls.set_names = ["sharekit:edusources"]
        cls.product_seeds = [
            {
                "state": "active",
                "set": "sharekit:edusources",
                "external_id": "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257",
                "title": "To be deleted",
                "language": "en",
                "learning_material": {
                    "study_vocabulary": ["applied-science"]  # remains intact
                }
            },
            {
                "state": "active",
                "set": "sharekit:edusources",
                "external_id": "63903863-6c93-4bda-b850-277f3c9ec00e",
                "title": "Should become 'Pim-pam-pet denken bij scheikunde'",
                "language": "nl",
                "learning_material": {
                    "study_vocabulary": ["applied-science"]  # gets replaced
                }
            }
        ]
        cls.file_seeds = [
            {
                "state": "active",
                "set": "sharekit:edusources",
                "external_id": "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257:8b714937aab9bda1005d8aa76c607e629b25d89e",
                "url": "https://www.youtube.com/watch?v=Zl59P5ZNX3M",
                "product_id": "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257",
            },
            {
                "state": "active",
                "set": "sharekit:edusources",
                "external_id": "63903863-6c93-4bda-b850-277f3c9ec00e:7ec8985621b50d7bf29b06cf4d413191d0a20bd4",
                "url": "https://surfsharekit.nl/objectstore/88c687c8-fbc4-4d69-a27d-45d9f30d642b",
                "product_id": "63903863-6c93-4bda-b850-277f3c9ec00e",
            },
            {
                "state": "active",
                "set": "sharekit:edusources",
                "external_id": "63903863-6c93-4bda-b850-277f3c9ec00e:339df213a16895868ba4bfc635b7d3348348e33a",
                "url": "https://surfsharekit.nl/objectstore/9f71f782-09de-48b1-a10f-15d882471df7",
                "product_id": "63903863-6c93-4bda-b850-277f3c9ec00e",
            },
            {
                "state": "active",
                "set": "sharekit:edusources",
                "external_id": "63903863-6c93-4bda-b850-277f3c9ec00e:ae362bbe89cae936c89aed50dfd6b7a1cb6bf03b",
                "url": "https://maken.wikiwijs.nl/94812/Macro_meso_micro#!page-2935729",
                "product_id": "63903863-6c93-4bda-b850-277f3c9ec00e",
            },
        ]
        cls.product_dataset, cls.product_dataset_version, cls.product_sets, cls.product_documents = (
            create_datatype_models("products", cls.set_names, cls.product_seeds, 2)
        )
        cls.files_dataset, cls.files_dataset_version, cls.files_sets, cls.files_documents = (
            create_datatype_models("files", cls.set_names, cls.file_seeds, 4)
        )
        cls.update_document = cls.product_documents[1]
        cls.update_document.pipeline["lookup_study_vocabulary_parents"] = {"success": True}
        cls.update_document.save()
        delete_document = cls.product_documents[0]
        delete_document.pipeline["lookup_study_vocabulary_parents"] = {"success": True}
        delete_document.save()

    @classmethod
    def load_sharekit_test_data(cls):
        # Load the data that we'll be sending to the webhook view
        delta_response = SharekitMetadataHarvestFactory.create(is_initial=False, number=0)
        content_type, delta = delta_response.content
        delta_records = delta["data"]
        cls.test_data = {
            "create": delta_records[2],
            "update": delta_records[1],
            "delete": delta_records[0]
        }
        cls.test_product_ids = {
            test_type: product_data["id"]
            for test_type, product_data in cls.test_data.items()
        }

    @classmethod
    def setUpTestData(cls):
        cls.load_product_test_data()
        cls.test_start_time = now()
        cls.webhook_url = reverse("product-webhook", args=("sharekit", "edusources", cls.webhook_secret,))
        cls.load_sharekit_test_data()
        cls.data_key = "attributes"
