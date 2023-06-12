from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User

from search_client import DocumentTypes
from core.models import DatasetVersion, Document


class TestDocumentView(TestCase):

    fixtures = ["datasets-history"]
    maxDiff = None

    format = None
    list_view_name = "v1:core:list-documents"
    detail_view_name = "v1:core:document-detail"
    expected_document_output = {
        "external_id": "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257",
        "published_at": "2016-09-02",
        "doi": None,
        "url": "https://www.youtube.com/watch?v=Zl59P5ZNX3M",
        "title": "Using a Vortex | Wageningen UR",
        "description": "Instruction on how to use a Vortex mixer",
        "language": "en",
        "copyright": "cc-by-40",
        "video": None,
        "harvest_source": "edusources",
        "previews": None,
        "files": [
            {
                "url": "https://www.youtube.com/watch?v=Zl59P5ZNX3M",
                "hash": "8b714937aab9bda1005d8aa76c607e629b25d89e",
                "title": "URL 1",
                "mime_type": "text/html"
            }
        ],
        "authors": [],
        "has_parts": [
            "part"
        ],
        "is_part_of": [
            "part"
        ],
        "keywords": [
            "Video",
            "Practicum clip",
            "Instructie clip"
        ],
        "provider": {"external_id": None, "id": None, "name": "SURFnet", "slug": None},
        "lom_educational_levels": [
            "WO"
        ],
        "studies": [],
        "disciplines": [],
        "ideas": [],
        "study_vocabulary": [],
        "technical_type": "website",
        "publishers": [
            "SURFnet"
        ],
        "consortium": None
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="supersurf")

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_list(self):
        list_url = reverse(self.list_view_name)
        response = self.client.get(list_url + "?page=1&page_size=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if not self.format:
            self.assertEqual(data["next"], "http://testserver/api/v1/document/?page=2&page_size=10")
        else:
            self.assertEqual(data["next"], f"http://testserver/api/v1/document/{self.format}/?page=2&page_size=10")
        self.assertIsNone(data["previous"])
        self.assertEqual(len(data["results"]), 10)
        self.assertEqual(data["count"], 12)

    def test_list_second_page(self):
        list_url = reverse(self.list_view_name)
        response = self.client.get(list_url + "?page=2&page_size=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if not self.format:
            self.assertEqual(data["previous"], "http://testserver/api/v1/document/?page_size=10")
        else:
            self.assertEqual(data["previous"], f"http://testserver/api/v1/document/{self.format}/?page_size=10")
        self.assertIsNone(data["next"])
        self.assertEqual(len(data["results"]), 2)
        self.assertEqual(data["count"], 12)

    def test_list_no_dataset_version(self):
        DatasetVersion.objects.all().delete()
        list_url = reverse(self.list_view_name)
        response = self.client.get(list_url + "?page=1&page_size=10")
        self.assertEqual(response.status_code, 417)
        data = response.json()
        self.assertEqual(data["detail"], "Missing a current dataset version to list data")

    def test_detail(self):
        detail_url = reverse(self.detail_view_name, args=("5be6dfeb-b9ad-41a8-b4f5-94b9438e4257",))
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if self.format == "raw":
            data.pop("properties")  # these are expected to change often and shouldn"t fail the tests
        self.assertEqual(data, self.expected_document_output)

    def test_detail_not_found(self):
        detail_url = reverse(self.detail_view_name, args=("does-not-exist",))
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["detail"], "Not found.")

    def test_detail_quoted_id(self):
        """
        This test checks whether Documents can be referenced with "/" or other URL characters in their reference.
        When making detail requests for such Documents the client should URL encode the "external_id"
        """
        document = Document.objects.get(reference="5be6dfeb-b9ad-41a8-b4f5-94b9438e4257")
        document.reference += "/1"
        document.save()
        detail_url = reverse(self.detail_view_name, args=("5be6dfeb-b9ad-41a8-b4f5-94b9438e4257%2F1",))
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

    def test_detail_no_dataset_version(self):
        DatasetVersion.objects.all().delete()
        detail_url = reverse(self.detail_view_name, args=("5be6dfeb-b9ad-41a8-b4f5-94b9438e4257",))
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 417)
        data = response.json()
        self.assertEqual(data["detail"], "Missing a current dataset version to retrieve data")


@override_settings(DOCUMENT_TYPE=DocumentTypes.RESEARCH_PRODUCT)
class TestResearchProductDocumentView(TestDocumentView):
    expected_document_output = {
        "external_id": "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257",
        "published_at": "2016-09-02",
        "doi": None,
        "url": "https://www.youtube.com/watch?v=Zl59P5ZNX3M",
        "title": "Using a Vortex | Wageningen UR",
        "description": "Instruction on how to use a Vortex mixer",
        "language": "en",
        "copyright": "cc-by-40",
        "video": None,
        "harvest_source": "edusources",
        "previews": None,
        "files": [
            {
                "url": "https://www.youtube.com/watch?v=Zl59P5ZNX3M",
                "hash": "8b714937aab9bda1005d8aa76c607e629b25d89e",
                "title": "URL 1",
                "mime_type": "text/html"
            }
        ],
        "authors": [],
        "has_parts": [
            "part"
        ],
        "is_part_of": [
            "part"
        ],
        "keywords": [
            "Video",
            "Practicum clip",
            "Instructie clip"
        ],
        "provider": "SURFnet",
        "type": "website",
        "research_object_type": None,
        "extension": None,
        "parties": [
            "SURFnet"
        ],
        "research_themes": [
            "research"
        ],
        "projects": [],
        "owners": [],
        "contacts": []
    }


class TestRawDocumentView(TestDocumentView):

    format = "raw"
    list_view_name = "v1:core:raw-documents"
    detail_view_name = "v1:core:raw-document-detail"
    expected_document_output = {
        "id": 222318,
        "created_at": "2020-02-17T10:53:24.388000Z",
        "modified_at": "2020-02-17T10:53:24.388000Z",
        "reference": "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257",
        "identity": None,
        "harvest_source": "edusources",
        "feed": "edusources"
    }


class TestMetadataDocumentView(TestDocumentView):

    format = "metadata"
    list_view_name = "v1:core:metadata-documents"
    detail_view_name = "v1:core:metadata-document-detail"
    expected_document_output = {
        "id": 222318,
        "reference": "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257",
        "language": "en",
        "created_at": "2020-02-17T10:53:24.388000Z",
        "modified_at": "2020-02-17T10:53:24.388000Z"
    }


@override_settings(DOCUMENT_TYPE=DocumentTypes.RESEARCH_PRODUCT)
class TestExtendedDocumentView(TestCase):

    fixtures = ["datasets-history"]
    expected_document_output = {
        "external_id": "5af0e26f-c4d2-4ddd-94ab-7dd0bd531751",
        "published_at": "2019",
        "doi": None,
        "url": "https://surfsharekit.nl/objectstore/182216be-31a2-43c3-b7de-e5dd355b09f7",
        "title": "Exercises 5",
        "description": "Fifth exercises of the course",
        "language": "en",
        "copyright": "cc-by-nc-40",
        "video": None,
        "harvest_source": "edusources",
        "previews": None,
        "files": [
            {
                "url": "https://surfsharekit.nl/objectstore/182216be-31a2-43c3-b7de-e5dd355b09f7",
                "hash": "0ed38cdc914e5e8a6aa1248438a1e2032a14b0de",
                "title": "40. Exercises 5.docx",
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            }
        ],
        "authors": [],
        "has_parts": [
            "part"
        ],
        "is_part_of": [
            "part"
        ],
        "keywords": [
            "exercise"
        ],
        "provider": "SURFnet",
        "type": "document",
        "research_object_type": None,
        "extension": {
            "id": "5af0e26f-c4d2-4ddd-94ab-7dd0bd531751",
            "is_addition": False
        },
        "parties": [
            "SURFnet"
        ],
        "research_themes": [
            "research"
        ],
        "projects": [],
        "owners": [],
        "contacts": []
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="supersurf")

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_list(self):
        list_url = reverse("v1:core:list-documents")
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        extension_document = next(
            (doc for doc in data["results"]
             if doc["external_id"] == "5af0e26f-c4d2-4ddd-94ab-7dd0bd531751")
        )
        self.assertEqual(
            extension_document, self.expected_document_output,
            "Expected Extension not to overwrite Document properties in Document API"
        )

    def test_detail(self):
        detail_url = reverse("v1:core:document-detail", args=("5af0e26f-c4d2-4ddd-94ab-7dd0bd531751",))
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            data, self.expected_document_output,
            "Expected Extension not to overwrite Document properties in Document API"
        )
