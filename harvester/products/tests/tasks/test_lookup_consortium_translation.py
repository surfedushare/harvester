from django.test import TestCase

from metadata.models import MetadataField, MetadataValue, MetadataTranslation
from testing.utils.factories import create_datatype_models
from products.tasks import lookup_consortium_translations
from products.models import ProductDocument


class TestLookupConsortiumTranslations(TestCase):

    fixtures = ["test-metadata-edusources"]

    @classmethod
    def setUpTestData(cls):
        consortium_field = MetadataField.objects.get(name="consortium.keyword")
        translation = MetadataTranslation.objects.create(en="SURF", nl="Stichting Universitaire Reken Faciliteiten")
        MetadataValue.objects.create(value="surf", translation=translation, field=consortium_field)

    def setUp(self) -> None:
        super().setUp()
        self.set_names = ["surf:testing"]
        self.seeds = [
            {
                "state": "active",
                "external_id": 1,
                "set": "surf:testing",
                "learning_material": {
                    "consortium": "surf"
                }
            },
            {
                "state": "active",
                "external_id": 2,
                "set": "surf:testing",
                "learning_material": {
                    "consortium": None
                }
            }
        ]
        self.dataset, self.dataset_version, self.sets, self.documents = create_datatype_models(
            "products", self.set_names,
            self.seeds, len(self.seeds)
        )

    def test_lookup_consortium_translations(self):
        lookup_consortium_translations("products", [doc.id for doc in self.documents])
        consortium_doc = ProductDocument.objects.get(identity="surf:testing:1")
        self.assertEqual(consortium_doc.derivatives, {
            "lookup_consortium_translations": {
                "consortium": {
                    "keyword": "surf",
                    "en": "SURF",
                    "nl": "Stichting Universitaire Reken Faciliteiten",
                }
            }
        })
        self.assertEqual(consortium_doc.pipeline, {
            "lookup_consortium_translations": {"success": True}
        })
        undefined = ProductDocument.objects.get(identity="surf:testing:2")
        self.assertEqual(undefined.derivatives, {
            "lookup_consortium_translations": {
                "consortium": {
                    "keyword": None,
                    "en": None,
                    "nl": None,
                }
            }
        })
        self.assertEqual(undefined.pipeline, {
            "lookup_consortium_translations": {"success": True}
        })
