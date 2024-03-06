from django.test import TestCase

from testing.utils.factories import create_datatype_models
from products.tasks import normalize_publisher_year
from products.models import ProductDocument


class TestNormalizePublisherYear(TestCase):

    fixtures = ["test-metadata-edusources"]

    def setUp(self) -> None:
        super().setUp()
        self.set_names = ["surf:testing"]
        self.seeds = [
            {
                "state": "active",
                "external_id": 1,
                "set": "surf:testing",
                "publisher_year": 1970,
            },
            {
                "state": "active",
                "external_id": 2,
                "set": "surf:testing",
                "publisher_year": 2022
            },
            {
                "state": "active",
                "external_id": 3,
                "set": "surf:testing",
                "publisher_year": None
            },
            {
                "state": "active",
                "external_id": 4,
                "set": "surf:testing",
                "publisher_year": 9999
            }
        ]
        self.dataset, self.dataset_version, self.sets, self.documents = create_datatype_models(
            "products", self.set_names,
            self.seeds, len(self.seeds)
        )

    def test_normalize_publisher_year(self):
        normalize_publisher_year("products", [doc.id for doc in self.documents])
        old_product = ProductDocument.objects.get(identity="surf:testing:1")
        self.assertEqual(old_product.derivatives, {
            "normalize_publisher_year": {"publisher_year_normalized": "older-than"}
        })
        self.assertEqual(old_product.pipeline, {
            "normalize_publisher_year": {"success": True}
        })
        new_product = ProductDocument.objects.get(identity="surf:testing:2")
        self.assertEqual(new_product.derivatives, {
            "normalize_publisher_year": {"publisher_year_normalized": "2022"}
        })
        self.assertEqual(new_product.pipeline, {
            "normalize_publisher_year": {"success": True}
        })
        undefined = ProductDocument.objects.get(identity="surf:testing:3")
        self.assertEqual(undefined.derivatives, {
            "normalize_publisher_year": {"publisher_year_normalized": None}
        })
        self.assertEqual(undefined.pipeline, {
            "normalize_publisher_year": {"success": True}
        })
        invalid = ProductDocument.objects.get(identity="surf:testing:4")
        self.assertEqual(invalid.derivatives, {
            "normalize_publisher_year": {"publisher_year_normalized": None}
        })
        self.assertEqual(invalid.pipeline, {
            "normalize_publisher_year": {"success": True}
        })
