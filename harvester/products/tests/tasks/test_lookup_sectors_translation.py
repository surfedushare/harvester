from django.test import TestCase

from metadata.models import MetadataField, MetadataValue, MetadataTranslation
from testing.utils.factories import create_datatype_models
from products.tasks import lookup_sectors_translations
from products.models import ProductDocument


class TestLookupSectorsTranslations(TestCase):

    fixtures = ["test-metadata"]

    @classmethod
    def setUpTestData(cls):
        sectors_field = MetadataField.objects.get(name="sectors.keyword")
        translation = MetadataTranslation.objects.create(
            en="Engineering and built environment sector",
            nl="Sector techniek en gebouwde omgeving"
        )
        MetadataValue.objects.create(value="tgo", translation=translation, field=sectors_field)

    def setUp(self) -> None:
        super().setUp()
        self.set_names = ["surf:testing"]
        self.seeds = [
            {
                "state": "active",
                "external_id": 1,
                "set": "surf:testing",
                "learning_material": {
                    "sectors": ["tgo"]
                }
            },
            {
                "state": "active",
                "external_id": 2,
                "set": "surf:testing",
                "learning_material": {
                    "sectors": []
                }
            }
        ]
        self.dataset, self.dataset_version, self.sets, self.documents = create_datatype_models(
            "products", self.set_names,
            self.seeds, len(self.seeds)
        )

    def test_lookup_sectors_translations(self):
        lookup_sectors_translations("products", [doc.id for doc in self.documents])
        sectors_doc = ProductDocument.objects.get(identity="surf:testing:1")
        self.assertEqual(sectors_doc.derivatives, {
            "lookup_sectors_translations": {
                "sectors": {
                    "keyword": ["tgo"],
                    "en": ["Engineering and built environment sector"],
                    "nl": ["Sector techniek en gebouwde omgeving"],
                }
            }
        })
        self.assertEqual(sectors_doc.pipeline, {
            "lookup_sectors_translations": {"success": True}
        })
        undefined = ProductDocument.objects.get(identity="surf:testing:2")
        self.assertEqual(undefined.derivatives, {
            "lookup_sectors_translations": {
                "sectors": {
                    "keyword": [],
                    "en": [],
                    "nl": [],
                }
            }
        })
        self.assertEqual(undefined.pipeline, {
            "lookup_sectors_translations": {"success": True}
        })
