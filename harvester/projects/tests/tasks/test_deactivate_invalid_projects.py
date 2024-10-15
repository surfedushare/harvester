from django.test import TestCase

from testing.utils.factories import create_datatype_models
from projects.tasks import deactivate_invalid_projects
from projects.models import ProjectDocument


class TestDeactivateInvalidProjects(TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.set_names = ["surf:testing"]
        self.seeds = [
            {
                "state": "active",
                "external_id": "1",
                "set": "surf:testing",
                "title": "Title 1",
                "description": "Description 1",
                "project_status": "finished",
                "keywords": ["valid", "keywords"]
            },
            {
                "state": "active",
                "external_id": 2,
                "set": "surf:testing",
                "title": "Title 2",
                "description": "Description 2",
                "project_status": "finished",
                "keywords": "invalid, keywords"
            },
            {
                "state": "active",
                "external_id": "3",
                "title": "Title 3",
                "description": "Description 3",
                "project_status": "finished",
                "set": "surf:testing",
            }
        ]
        self.dataset, self.dataset_version, self.sets, self.documents = create_datatype_models(
            "projects", self.set_names,
            self.seeds, len(self.seeds)
        )

    maxDiff = None

    def test_deactivate_invalid_products(self):
        deactivate_invalid_projects("projects", [doc.id for doc in self.documents])

        valid_document = ProjectDocument.objects.get(identity="surf:testing:1")
        self.assertEqual(valid_document.pipeline, {
            "deactivate_invalid_projects": {"success": True, "validation": None}
        })
        self.assertEqual(valid_document.state, ProjectDocument.States.ACTIVE)

        invalid_document = ProjectDocument.objects.get(identity="surf:testing:2")
        self.assertTrue(invalid_document.pipeline["deactivate_invalid_projects"]["success"])
        validation_errors = invalid_document.pipeline["deactivate_invalid_projects"]["validation"]
        self.assertTrue(validation_errors.startswith("2 validation errors for "))
        self.assertEqual(invalid_document.state, ProjectDocument.States.INACTIVE)

        default_document = ProjectDocument.objects.get(identity="surf:testing:3")
        self.assertEqual(default_document.pipeline, {
            "deactivate_invalid_projects": {"success": True, "validation": None}
        })
        self.assertEqual(default_document.state, ProjectDocument.States.ACTIVE)
