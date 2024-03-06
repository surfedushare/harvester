from django.test import TestCase

from testing.utils.factories import create_datatype_models
from products.tasks import normalize_disciplines
from products.models import ProductDocument


class TestNormalizeDisciplines(TestCase):

    fixtures = ["test-metadata-edusources"]

    def setUp(self) -> None:
        super().setUp()
        self.set_names = ["surf:testing"]
        self.seeds = [
            {
                "state": "active",
                "external_id": 1,
                "set": "surf:testing",
                "learning_material": {
                    "disciplines": [
                        "c001f86a-4f8f-4420-bd78-381c615ecedc"  # name=Aardrijkskunde
                    ]
                }
            },
            {
                "state": "active",
                "external_id": 2,
                "set": "surf:testing",
                "learning_material": {
                    "disciplines": [
                        "92161d11-91ce-48e2-b79a-8aa2df8b7022"  # name=Bedrijfskunde
                    ]
                }
            },
            {
                "state": "active",
                "external_id": 3,
                "set": "surf:testing",
                "learning_material": {
                    "disciplines": []
                }
            }
        ]
        self.dataset, self.dataset_version, self.sets, self.documents = create_datatype_models(
            "products", self.set_names,
            self.seeds, len(self.seeds)
        )

    def test_normalize_disciplines(self):
        normalize_disciplines("products", [doc.id for doc in self.documents])
        earth_and_environment = ProductDocument.objects.get(identity="surf:testing:1")
        self.assertEqual(earth_and_environment.derivatives, {
            "normalize_disciplines": {"learning_material_disciplines_normalized": ["aarde_milieu"]}
        })
        self.assertEqual(earth_and_environment.pipeline, {
            "normalize_disciplines": {"success": True}
        })
        economy_and_business = ProductDocument.objects.get(identity="surf:testing:2")
        self.assertEqual(economy_and_business.derivatives, {
            "normalize_disciplines": {"learning_material_disciplines_normalized": ["economie_bedrijf"]}
        })
        self.assertEqual(economy_and_business.pipeline, {
            "normalize_disciplines": {"success": True}
        })
        undefined = ProductDocument.objects.get(identity="surf:testing:3")
        self.assertEqual(undefined.derivatives, {
            "normalize_disciplines": {"learning_material_disciplines_normalized": []}
        })
        self.assertEqual(undefined.pipeline, {
            "normalize_disciplines": {"success": True}
        })
