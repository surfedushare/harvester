from django.test import TestCase

from testing.utils.factories import create_datatype_models
from organizations.tasks import deactivate_invalid_organizations
from organizations.models import OrganizationDocument


class TestDeactivateInvalidOrganizations(TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.set_names = ["surf:testing"]
        self.seeds = [
            {
                "state": "active",
                "external_id": "1",
                "set": "surf:testing",
                "name": "Name 1",
                "ror": "roarrrr",
                "type": "organisation"
            },
            {
                "state": "active",
                "external_id": 2,
                "set": "surf:testing",
                "name": "Name 2",
                "ror": 2
            },
            {
                "state": "active",
                "external_id": "3",
                "set": "surf:testing",
                "name": "Name 2",
                "type": "organization"
            }
        ]
        self.dataset, self.dataset_version, self.sets, self.documents = create_datatype_models(
            "organizations", self.set_names,
            self.seeds, len(self.seeds)
        )

    def test_deactivate_invalid_organizations(self):
        deactivate_invalid_organizations("organizations", [doc.id for doc in self.documents])

        valid_document = OrganizationDocument.objects.get(identity="surf:testing:1")
        self.assertEqual(valid_document.pipeline, {
            "deactivate_invalid_organizations": {"success": True, "validation": None}
        })
        self.assertEqual(valid_document.state, OrganizationDocument.States.ACTIVE)
        self.assertEqual(valid_document.properties["state"], OrganizationDocument.States.ACTIVE)

        invalid_document = OrganizationDocument.objects.get(identity="surf:testing:2")
        self.assertTrue(invalid_document.pipeline["deactivate_invalid_organizations"]["success"])
        validation_errors = invalid_document.pipeline["deactivate_invalid_organizations"]["validation"]
        self.assertTrue(validation_errors.startswith("2 validation errors for "))
        self.assertEqual(invalid_document.state, OrganizationDocument.States.INACTIVE)
        self.assertEqual(invalid_document.properties["state"], OrganizationDocument.States.INACTIVE)

        default_document = OrganizationDocument.objects.get(identity="surf:testing:3")
        self.assertEqual(default_document.pipeline, {
            "deactivate_invalid_organizations": {"success": True, "validation": None}
        })
        self.assertEqual(default_document.state, OrganizationDocument.States.ACTIVE)
        self.assertEqual(default_document.properties["state"], OrganizationDocument.States.ACTIVE)
