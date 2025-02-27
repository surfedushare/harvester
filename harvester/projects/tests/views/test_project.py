from datetime import datetime

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User

from search_client.constants import Platforms
from projects.models import DatasetVersion, ProjectDocument


@override_settings(PLATFORM=Platforms.PUBLINOVA)
class TestProjectView(TestCase):

    fixtures = ["test-project-document"]
    maxDiff = None

    format = None
    list_view_name = "v1:projects:list-projects"
    detail_view_name = "v1:projects:project-detail"
    expected_document_output = {
        "entity": "projects",
        "srn": "buas:project:133ce0c9-9dd6-44b8-b798-3b524f17bce0",
        "set": "buas:project",
        "state": "active",
        "external_id": "133ce0c9-9dd6-44b8-b798-3b524f17bce0",
        "score": 0.0,
        "provider": "Breda University of Applied Sciences",
        "title": "K2K Consortium development zero-emissions tourism mobility",
        "description": "Client: Netherlands Enterprise Agency (RVO.nl) / Partners for International Business (PIB)",
        "project_status": "finished",
        "started_at": "2017-01-01",
        "ended_at": "2019-12-31",
        "coordinates": [],
        "goal": None,
        "approach": None,
        "results": None,
        "keywords": [
            "Zero-emissions",
            "tourism",
            "mobility",
            "transport",
            "sustainable tourism",
            "CSTT",
            "Centre for Sustainability, Tourism and Transport"
        ],
        "products": [
            "e3a6cbe7-1606-433d-8bca-7d42e08305c2",
            "e4f96a7c-029b-42b3-8039-c184e31c76d0"
        ],
        "previews": None,
        "persons": [
            {
                "name": "Eggie",
                "email": None,
                "external_id": "4f3e10ea-c09b-4f9e-98bb-7407d1340112"
            },
            {
                "name": "Paultje",
                "email": None,
                "external_id": "97ee5bd3-2145-4a4a-9a61-827e2ec839ef"
            }
        ],
        "contacts": [
            {
                "name": "Eggie",
                "email": None,
                "external_id": "4f3e10ea-c09b-4f9e-98bb-7407d1340112"
            }
        ],
        "owners": [
            {
                "name": "Eggie",
                "email": None,
                "external_id": "4f3e10ea-c09b-4f9e-98bb-7407d1340112"
            }
        ],
        "parties": [
            "Camptoo",
            "DEOdrive",
            "Dutch Innovation Centre for Electric Road Transport (Dutch-INCERT)",
            "Emodz",
            "EMOSS",
            "EVConsult",
            "Hansa Green Tour",
            "Rijksdienst voor Ondernemend Nederland (RVO.nl)"
        ],
        "themes": [],
        "research_themes": [],
        "sia_project_reference": None
    }

    expected_document_count = 13  # 1 original, 15 copies and minus 3 deletes

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="supersurf")
        create_time = datetime(year=2000, month=1, day=1)
        delete_time = datetime(year=2024, month=1, day=1)
        # We duplicate the Document data a bunch to create larger responses
        document = ProjectDocument.objects.first()
        identity = document.identity
        for ix in range(0, 15):
            document.id = None
            document.pk = None
            document.identity = f"{identity}-{ix}"
            if not ix % 5:
                document.state = ProjectDocument.States.DELETED
                document.properties["state"] = ProjectDocument.States.DELETED
                document.set_metadata(current_time=delete_time)
            else:
                document.state = ProjectDocument.States.ACTIVE
                document.properties["state"] = ProjectDocument.States.ACTIVE
                document.set_metadata(current_time=create_time)
            document.save()

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_list(self):
        list_url = reverse(self.list_view_name)
        response = self.client.get(list_url + "?page=1&page_size=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if not self.format:
            self.assertEqual(data["next"], "http://testserver/api/v1/project/?page=2&page_size=10")
        else:
            self.assertEqual(data["next"], f"http://testserver/api/v1/project/{self.format}/?page=2&page_size=10")
        self.assertIsNone(data["previous"])
        self.assertEqual(len(data["results"]), 10)
        self.assertEqual(data["count"], self.expected_document_count)

    def test_list_second_page(self):
        list_url = reverse(self.list_view_name)
        response = self.client.get(list_url + "?page=2&page_size=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if not self.format:
            self.assertEqual(data["previous"], "http://testserver/api/v1/project/?page_size=10")
        else:
            self.assertEqual(data["previous"], f"http://testserver/api/v1/project/{self.format}/?page_size=10")
        self.assertIsNone(data["next"])
        self.assertEqual(len(data["results"]), self.expected_document_count - 10)
        self.assertEqual(data["count"], self.expected_document_count)

    def test_list_no_dataset_version(self):
        DatasetVersion.objects.all().update(is_current=False)
        list_url = reverse(self.list_view_name)
        response = self.client.get(list_url + "?page=1&page_size=10")
        self.assertEqual(response.status_code, 417)
        data = response.json()
        self.assertEqual(data["detail"], "Missing a current dataset version to list data")

    def test_detail(self):
        detail_url = reverse(self.detail_view_name, args=("buas:project:133ce0c9-9dd6-44b8-b798-3b524f17bce0",))
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if self.format == "raw":
            # These are expected to change often in the raw data format and shouldn't fail the tests
            data.pop("properties")
            data.pop("derivatives")
            data.pop("transform")
        self.assertEqual(data, self.expected_document_output)

    def test_detail_not_found(self):
        detail_url = reverse(self.detail_view_name, args=("does-not-exist",))
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["detail"], "No ProjectDocument matches the given query.")

    def test_detail_quoted_id(self):
        """
        This test checks whether Documents can be referenced with "/" or other URL characters in their reference.
        When making detail requests for such Documents the client should URL encode the "external_id"
        """
        document = ProjectDocument.objects.get(identity="buas:project:133ce0c9-9dd6-44b8-b798-3b524f17bce0")
        document.identity += "/1"
        document.save()
        detail_url = reverse(
            self.detail_view_name,
            args=("buas:project:133ce0c9-9dd6-44b8-b798-3b524f17bce0%2F1",)
        )
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

    def test_detail_no_dataset_version(self):
        DatasetVersion.objects.all().update(is_current=False)
        detail_url = reverse(self.detail_view_name, args=("sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e",))
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 417)
        data = response.json()
        self.assertEqual(data["detail"], "Missing a current dataset version to retrieve data")


@override_settings(PLATFORM=Platforms.PUBLINOVA)
class TestRawProductView(TestProjectView):

    format = "raw"
    list_view_name = "v1:projects:raw-projects"
    detail_view_name = "v1:projects:raw-project-detail"
    expected_document_output = {
        "id": 1,
        "created_at": "2025-02-13T01:22:06.623000Z",
        "modified_at": "2025-02-13T01:23:30.702000Z",
        "reference": None,
        "identity": "buas:project:133ce0c9-9dd6-44b8-b798-3b524f17bce0",
        "state": "active",
        "metadata": {
            "hash": "39fb07b6b421be440b118e8334f57b22f3735997",
            "provider": "Breda University of Applied Sciences",
            "created_at": "2025-02-13T01:22:06.614000Z",
            "deleted_at": "2025-02-13T01:23:30.702000Z",
            "modified_at": "2025-02-13T01:23:30.702000Z"
        },
    }
    expected_document_count = 16  # 1 original and 15 copies including all deletes


@override_settings(PLATFORM=Platforms.PUBLINOVA)
class TestMetadataProductView(TestProjectView):

    format = "metadata"
    list_view_name = "v1:projects:metadata-projects"
    detail_view_name = "v1:projects:metadata-project-detail"
    expected_document_output = {
        "id": 1,
        "state": "active",
        "srn": "buas:project:133ce0c9-9dd6-44b8-b798-3b524f17bce0",
        "title": "K2K Consortium development zero-emissions tourism mobility",
        "reference": "133ce0c9-9dd6-44b8-b798-3b524f17bce0",
        "created_at": "2025-02-13T01:22:06.614000Z",
        "modified_at": "2025-02-13T01:23:30.702000Z"
    }
