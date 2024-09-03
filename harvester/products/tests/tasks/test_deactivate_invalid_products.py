from django.test import TestCase

from testing.utils.factories import create_datatype_models
from products.tasks import deactivate_invalid_products
from products.models import ProductDocument


class TestDeactivateInvalidProducts(TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.set_names = ["surf:testing"]
        self.seeds = [
            {
                "state": "active",
                "external_id": "1",
                "set": "surf:testing",
                "keywords": ["valid", "keywords"]
            },
            {
                "state": "active",
                "external_id": 2,
                "set": "surf:testing",
                "keywords": "invalid, keywords"
            },
            {
                "state": "active",
                "external_id": "3",
                "set": "surf:testing",
            }
        ]
        self.dataset, self.dataset_version, self.sets, self.documents = create_datatype_models(
            "products", self.set_names,
            self.seeds, len(self.seeds)
        )

    def test_deactivate_invalid_products(self):
        deactivate_invalid_products("products", [doc.id for doc in self.documents])

        valid_document = ProductDocument.objects.get(identity="surf:testing:1")
        self.assertEqual(valid_document.pipeline, {
            "deactivate_invalid_products": {"success": True, "validation": None}
        })
        self.assertEqual(valid_document.state, ProductDocument.States.ACTIVE)

        invalid_document = ProductDocument.objects.get(identity="surf:testing:2")
        self.assertTrue(invalid_document.pipeline["deactivate_invalid_products"]["success"])
        validation_errors = invalid_document.pipeline["deactivate_invalid_products"]["validation"]
        self.assertTrue(validation_errors.startswith("2 validation errors for "))
        self.assertEqual(invalid_document.state, ProductDocument.States.INACTIVE)

        default_document = ProductDocument.objects.get(identity="surf:testing:3")
        self.assertEqual(default_document.pipeline, {
            "deactivate_invalid_products": {"success": True, "validation": None}
        })
        self.assertEqual(default_document.state, ProductDocument.States.ACTIVE)
