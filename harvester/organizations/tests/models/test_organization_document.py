from django.test import TestCase

from organizations.models import OrganizationDocument


class OrganizationDocumentTestCase(TestCase):

    fixtures = ["test-organization-document.json"]

    def test_to_search(self):
        organization = OrganizationDocument.objects.get(id=1)
        organization_search = organization.to_search()
        self.assertEqual(organization_search, {
            "_id": "sharekit:nppo:7c2a6784-4d18-472e-bf5e-f3a61cd66fae",
            "ror": None,
            "set": "sharekit:nppo",
            "srn": "sharekit:nppo:7c2a6784-4d18-472e-bf5e-f3a61cd66fae",
            "name": "Toegang tot het Recht",
            "type": "lectorate",
            "state": "active",
            "members": [],
            "parents": [
                {
                    "srn": "sharekit:nppo:66a0079d-c8c2-4bf1-93b9-a2133aa57524",
                    "name": "Kenniscentrum Sociale Innovatie"
                }
            ],
            "provider": "SURFSharekit",
            "secretary": None,
            "description": "Justice for ALL",
            "external_id": "7c2a6784-4d18-472e-bf5e-f3a61cd66fae",
            "overwrite": None,
            "metrics": None,
            "suggest_phrase": "Justice for ALL",
            "suggest_completion": [
                "Toegang tot het Recht",
                "Justice",
                "for",
                "ALL"
            ]
        })
