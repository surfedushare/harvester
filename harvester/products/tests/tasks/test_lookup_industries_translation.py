from django.test import TestCase

from metadata.models import MetadataField, MetadataValue, MetadataTranslation
from testing.utils.factories import create_datatype_models
from products.tasks import lookup_industries_translations
from products.models import ProductDocument


class TestLookupIndustriesTranslations(TestCase):

    fixtures = ["test-metadata"]

    @classmethod
    def setUpTestData(cls):
        industries_field = MetadataField.objects.get(name="industries.keyword")
        translation = MetadataTranslation.objects.create(en="SURF", nl="Stichting Universitaire Reken Faciliteiten")
        MetadataValue.objects.create(value="surf", translation=translation, field=industries_field)

    def setUp(self) -> None:
        super().setUp()
        self.set_names = ["surf:testing"]
        self.seeds = [
            {
                "state": "active",
                "external_id": 1,
                "set": "surf:testing",
                "learning_material": {
                    "industries": ["surf"]
                }
            },
            {
                "state": "active",
                "external_id": 2,
                "set": "surf:testing",
                "learning_material": {
                    "industries": []
                }
            }
        ]
        self.dataset, self.dataset_version, self.sets, self.documents = create_datatype_models(
            "products", self.set_names,
            self.seeds, len(self.seeds)
        )

    def test_lookup_industries_translations(self):
        lookup_industries_translations("products", [doc.id for doc in self.documents])
        industries_doc = ProductDocument.objects.get(identity="surf:testing:1")
        self.assertEqual(industries_doc.derivatives, {
            "lookup_industries_translations": {
                "industries": {
                    "keyword": ["surf"],
                    "en": ["SURF"],
                    "nl": ["Stichting Universitaire Reken Faciliteiten"],
                }
            }
        })
        self.assertEqual(industries_doc.pipeline, {
            "lookup_industries_translations": {"success": True}
        })
        undefined = ProductDocument.objects.get(identity="surf:testing:2")
        self.assertEqual(undefined.derivatives, {
            "lookup_industries_translations": {
                "industries": {
                    "keyword": [],
                    "en": [],
                    "nl": [],
                }
            }
        })
        self.assertEqual(undefined.pipeline, {
            "lookup_industries_translations": {"success": True}
        })
