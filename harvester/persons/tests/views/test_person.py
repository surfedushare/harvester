from datetime import datetime

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User

from search_client.constants import Platforms
from persons.models import DatasetVersion, PersonDocument


@override_settings(PLATFORM=Platforms.PUBLINOVA)
class TestPersonView(TestCase):

    fixtures = ["test-person-document"]
    maxDiff = None

    format = None
    list_view_name = "v1:persons:list-persons"
    detail_view_name = "v1:persons:person-detail"
    expected_document_output = {
        "entity": "persons",
        "srn": "hku:person:1",
        "set": "hku:person",
        "state": "active",
        "external_id": "1",
        "score": 0.0,
        "provider": "Hogeschool voor de Kunsten",
        "name": "Pietje Puk",
        "first_name": None,
        "last_name": "Puk",
        "prefix": None,
        "initials": None,
        "email": "pietje.puk@hku.nl",
        "phone": None,
        "photo_url": "https://octo.hku.nl/octo/repository/getfile?id=FIwGwx6hxCY&version=transcoded",
        "description": "<p>Pietje Puk is a researcher and designer</p>",
        "isni": None,
        "skills": [
            "skills-yo"
        ],
        "organizations": [],
        "is_employed": None,
        "job_title": None,
        "parties": [],
        "title": "MA",
        "themes": [
            "Taal, Cultuur en Kunsten",
            "Techniek"
        ],
        "orcid": "0000-0000-0000-0001",
        "dai": None
    }
    expected_document_count = 13  # 1 original, 15 copies and minus 3 deletes

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="supersurf")
        create_time = datetime(year=2000, month=1, day=1)
        delete_time = datetime(year=2024, month=1, day=1)
        # We duplicate the Document data a bunch to create larger responses
        document = PersonDocument.objects.first()
        identity = document.identity
        for ix in range(0, 15):
            document.id = None
            document.pk = None
            document.identity = f"{identity}-{ix}"
            if not ix % 5:
                document.state = PersonDocument.States.DELETED
                document.properties["state"] = PersonDocument.States.DELETED
                document.set_metadata(current_time=delete_time)
            else:
                document.state = PersonDocument.States.ACTIVE
                document.properties["state"] = PersonDocument.States.ACTIVE
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
            self.assertEqual(data["next"], "http://testserver/api/v1/person/?page=2&page_size=10")
        else:
            self.assertEqual(data["next"], f"http://testserver/api/v1/person/{self.format}/?page=2&page_size=10")
        self.assertIsNone(data["previous"])
        self.assertEqual(len(data["results"]), 10)
        self.assertEqual(data["count"], self.expected_document_count)

    def test_list_second_page(self):
        list_url = reverse(self.list_view_name)
        response = self.client.get(list_url + "?page=2&page_size=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if not self.format:
            self.assertEqual(data["previous"], "http://testserver/api/v1/person/?page_size=10")
        else:
            self.assertEqual(data["previous"], f"http://testserver/api/v1/person/{self.format}/?page_size=10")
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
        detail_url = reverse(self.detail_view_name, args=("hku:person:1",))
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if self.format == "raw":
            # These are expected to change often in the raw data format and shouldn't fail the tests
            data.pop("properties")
            data.pop("derivatives")
        self.assertEqual(data, self.expected_document_output)

    def test_detail_not_found(self):
        detail_url = reverse(self.detail_view_name, args=("does-not-exist",))
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["detail"], "No PersonDocument matches the given query.")

    def test_detail_quoted_id(self):
        """
        This test checks whether Documents can be referenced with "/" or other URL characters in their reference.
        When making detail requests for such Documents the client should URL encode the "external_id"
        """
        document = PersonDocument.objects.get(identity="hku:person:1")
        document.identity += "/1"
        document.save()
        detail_url = reverse(
            self.detail_view_name,
            args=("hku:person:1%2F1",)
        )
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

    def test_detail_no_dataset_version(self):
        DatasetVersion.objects.all().update(is_current=False)
        detail_url = reverse(self.detail_view_name, args=("hku:person:1",))
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 417)
        data = response.json()
        self.assertEqual(data["detail"], "Missing a current dataset version to retrieve data")


@override_settings(PLATFORM=Platforms.PUBLINOVA)
class TestRawProductView(TestPersonView):

    format = "raw"
    list_view_name = "v1:persons:raw-persons"
    detail_view_name = "v1:persons:raw-person-detail"
    expected_document_output = {
        "id": 1,
        "created_at": "2025-02-13T01:22:06.623000Z",
        "modified_at": "2025-02-13T01:23:30.702000Z",
        "reference": None,
        "identity": "hku:person:1",
        "state": "active",
        "metadata": {
            "hash": "dfafb69f08517a82a073b25e217bec57356f97e9",
            "provider": "Hogeschool voor de Kunsten",
            "created_at": "2025-02-13T01:22:06.614000Z",
            "deleted_at": None,
            "modified_at": "2025-02-13T01:23:30.702000Z"
        }
    }
    expected_document_count = 16  # 1 original and 15 copies including all deletes


@override_settings(PLATFORM=Platforms.PUBLINOVA)
class TestMetadataProductView(TestPersonView):

    format = "metadata"
    list_view_name = "v1:persons:metadata-persons"
    detail_view_name = "v1:persons:metadata-person-detail"
    expected_document_output = {
        "id": 1,
        "state": "active",
        "srn": "hku:person:1",
        "name": "Pietje Puk",
        "reference": "1",
        "created_at": "2025-02-13T01:22:06.614000Z",
        "modified_at": "2025-02-13T01:23:30.702000Z"
    }
