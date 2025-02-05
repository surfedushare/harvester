from django.test import TestCase

from testing.utils.factories import create_datatype_models

from core.tasks import deactivate_invalid_documents
from testing.models import TestDocument


class TestDeactivateInvalidDocuments(TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.set_names = ["surf:testing"]
        self.seeds = [
            {
                "state": "active",
                "external_id": "1",
                "set": "surf:testing",
                "url": "https://example.com",
                "title": "An interesting URL",
                "access_rights": "OpenAccess",
            },
            {
                "state": "active",
                "external_id": 2,
                "set": "surf:testing",
                "title": "An interesting URL",
                "access_rights": "OpenAccess",
            },
            {
                "state": "active",
                "external_id": "3",
                "set": "surf:testing",
                "url": "https://example.com",
            }
        ]
        self.dataset, self.dataset_version, self.sets, self.documents = create_datatype_models(
            "testing", self.set_names,
            self.seeds, len(self.seeds)
        )

    def test_deactivate_invalid_documents(self):
        deactivate_invalid_documents("testing", [doc.id for doc in self.documents])

        valid_document = TestDocument.objects.get(identity="surf:testing:1")
        self.assertEqual(valid_document.pipeline, {
            "deactivate_invalid_documents": {"success": True, "validation": None}
        })
        self.assertEqual(valid_document.state, TestDocument.States.ACTIVE)
        self.assertEqual(valid_document.properties["state"], TestDocument.States.ACTIVE)

        invalid_document = TestDocument.objects.get(identity="surf:testing:2")
        self.assertTrue(invalid_document.pipeline["deactivate_invalid_documents"]["success"])
        validation_errors = invalid_document.pipeline["deactivate_invalid_documents"]["validation"]
        self.assertTrue(validation_errors.startswith("2 validation errors for "))
        self.assertEqual(invalid_document.state, TestDocument.States.INACTIVE)
        self.assertEqual(invalid_document.properties["state"], TestDocument.States.INACTIVE)

        default_document = TestDocument.objects.get(identity="surf:testing:3")
        self.assertEqual(default_document.pipeline, {
            "deactivate_invalid_documents": {"success": True, "validation": None}
        })
        self.assertEqual(default_document.state, TestDocument.States.ACTIVE)
        self.assertEqual(default_document.properties["state"], TestDocument.States.ACTIVE)
