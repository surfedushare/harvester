from django.test import TestCase

from testing.utils.factories import create_datatype_models
from products.tasks import lookup_study_vocabulary_parents
from products.models import ProductDocument


class TestNormalizeDisciplines(TestCase):

    fixtures = ["test-study-vocabulary"]

    def setUp(self) -> None:
        super().setUp()
        self.set_names = ["surf:testing"]
        self.seeds = [
            {
                "state": "active",
                "external_id": 1,
                "set": "surf:testing",
                "learning_material": {
                    "study_vocabulary": [
                        # name=Waarde van informatie/data
                        "http://purl.edustandaard.nl/concept/c2d0aee0-19be-47f0-85b0-90ac17cd22c5",
                        # name=Samenwerken (in teams)
                        "http://purl.edustandaard.nl/concept/5273fae8-2571-43a0-9942-93aaea79053c"
                    ]
                }
            },
            {
                "state": "active",
                "external_id": 2,
                "set": "surf:testing",
                "learning_material": {
                    "study_vocabulary": [
                        # name=Kritisch beoordelen
                        "http://purl.edustandaard.nl/concept/f5e496d1-1585-4c7f-b15f-2345cd830877"
                    ]
                }
            },
            {
                "state": "active",
                "external_id": 3,
                "set": "surf:testing",
                "learning_material": {
                    "study_vocabulary": []
                }
            }
        ]
        self.dataset, self.dataset_version, self.sets, self.documents = create_datatype_models(
            "products", self.set_names,
            self.seeds, 3
        )

    def test_lookup_study_vocabulary_parents(self):
        lookup_study_vocabulary_parents("products", [doc.id for doc in self.documents])
        doc_1 = ProductDocument.objects.get(identity="surf:testing:1")
        self.assertEqual(doc_1.derivatives, {
            "lookup_study_vocabulary_parents": {"study_vocabulary": [
                # name=Oriënteren en specificeren
                "http://purl.edustandaard.nl/concept/2b1ad07f-d8b0-49ab-b4d2-eecf319f4001",
                # name=Samenwerken (in teams)
                "http://purl.edustandaard.nl/concept/5273fae8-2571-43a0-9942-93aaea79053c",
                # name=Oriënteren op informatielandschap
                "http://purl.edustandaard.nl/concept/8c08655f-04ab-4866-ba84-f564cbfc9baa",
                # name=Waarde van informatie/data
                "http://purl.edustandaard.nl/concept/c2d0aee0-19be-47f0-85b0-90ac17cd22c5",
                # name=Organiseren en verwerken
                "http://purl.edustandaard.nl/concept/c7854b24-1331-4418-b6cb-a44bfc960ed8",
                "informatievaardigheid"
            ]}
        }, "Expected all parents of all study vocabulary terms to get added without duplications")
        self.assertEqual(doc_1.pipeline, {
            "lookup_study_vocabulary_parents": {"success": True}
        })
        doc_2 = ProductDocument.objects.get(identity="surf:testing:2")
        self.assertEqual(doc_2.derivatives, {
            "lookup_study_vocabulary_parents": {"study_vocabulary": [
                # name=Kritisch beoordelen
                "http://purl.edustandaard.nl/concept/f5e496d1-1585-4c7f-b15f-2345cd830877",
                "informatievaardigheid"
            ]}
        }, "Expected parent of study vocabulary term to get added")
        self.assertEqual(doc_2.pipeline, {
            "lookup_study_vocabulary_parents": {"success": True}
        })
        doc_3 = ProductDocument.objects.get(identity="surf:testing:3")
        self.assertEqual(doc_3.derivatives, {
            "lookup_study_vocabulary_parents": {"study_vocabulary": []}
        }, "Expected empty list when no study vocabulary terms were specified")
        self.assertEqual(doc_3.pipeline, {
            "lookup_study_vocabulary_parents": {"success": True}
        })
