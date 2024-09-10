from datetime import datetime

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User

from search_client.constants import Platforms
from products.models import DatasetVersion, ProductDocument


class TestDocumentView(TestCase):

    fixtures = ["test-product-document"]
    maxDiff = None

    format = None
    list_view_name = "v1:products:list-products"
    detail_view_name = "v1:products:product-detail"
    expected_document_output = {
        "srn": "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e",
        "set": "sharekit:edusources",
        "external_id": "63903863-6c93-4bda-b850-277f3c9ec00e",
        "state": "active",
        "entity": "products",
        "published_at": "2017-09-27",
        "modified_at": "2021-04-15",
        "url": "https://surfsharekit.nl/objectstore/88c687c8-fbc4-4d69-a27d-45d9f30d642b",
        "title": "Didactiek van macro-meso-micro denken bij scheikunde",
        "description": "Geen samenvatting",
        "language": "nl",
        "copyright": "cc-by-sa-40",
        "video": None,
        "harvest_source": "edusources",
        "previews": None,
        "files": [
            {
                "srn": "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e:"
                       "7ec8985621b50d7bf29b06cf4d413191d0a20bd4",
                "url": "https://surfsharekit.nl/objectstore/88c687c8-fbc4-4d69-a27d-45d9f30d642b",
                "hash": "7ec8985621b50d7bf29b06cf4d413191d0a20bd4",
                "type": "document",
                "state": "active",
                "title": "IMSCP_94812.zip",
                "is_link": False,
                "priority": 0,
                "copyright": "cc-by-sa-40",
                "mime_type": "application/x-zip",
                "access_rights": "OpenAccess",
                "previews": None,
                "video": None,
            },
            {
                "srn": "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e:"
                       "339df213a16895868ba4bfc635b7d3348348e33a",
                "url": "https://surfsharekit.nl/objectstore/9f71f782-09de-48b1-a10f-15d882471df7",
                "hash": "339df213a16895868ba4bfc635b7d3348348e33a",
                "type": "document",
                "state": "active",
                "title": "Didactiek van macro-meso-micro denken bij scheikunde.pdf",
                "is_link": False,
                "priority": 0,
                "copyright": "cc-by-sa-40",
                "mime_type": "application/pdf",
                "access_rights": "OpenAccess",
                "previews": {
                    "preview": "https://surfpol-harvester-content-prod.s3.amazonaws.com/thumbnails/files/previews/"
                               "pdf/20240219154612151932.9f71f782-09de-48b1-a10f-15d882471df7-thumbnail-400x300.png",
                    "full_size": "https://surfpol-harvester-content-prod.s3.amazonaws.com/files/previews/"
                                 "pdf/20240219154612151932.9f71f782-09de-48b1-a10f-15d882471df7.png",
                    "preview_small": "https://surfpol-harvester-content-prod.s3.amazonaws.com/thumbnails/"
                                     "files/previews/pdf/20240219154612151932.9f71f782-09de-48b1-a10f-15d882471df7"
                                     "-thumbnail-200x150.png"
                },
                "video": None,
            },
            {
                "srn": "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e:"
                       "ae362bbe89cae936c89aed50dfd6b7a1cb6bf03b",
                "url": "https://maken.wikiwijs.nl/94812/Macro_meso_micro#!page-2935729",
                "hash": "ae362bbe89cae936c89aed50dfd6b7a1cb6bf03b",
                "type": "website",
                "state": "active",
                "title": "URL 1",
                "is_link": True,
                "priority": 0,
                "copyright": "cc-by-sa-40",
                "mime_type": "text/html",
                "access_rights": "OpenAccess",
                "previews": None,
                "video": None,
            }
        ],
        "aggregation_level": "4",
        "authors": [
            {
                "dai": None,
                "isni": None,
                "name": "Ruud Kok",
                "email": None,
                "orcid": None,
                "external_id": "83e7c163-075e-4eb2-8247-d975cf047dba",
                "is_external": None,
            },
            {
                "dai": None,
                "isni": None,
                "name": "Astrid Bulte",
                "email": None,
                "orcid": None,
                "external_id": "1174c1b9-f010-4a0a-98c0-2ceeefd0b506",
                "is_external": None,
            },
            {
                "dai": None,
                "isni": None,
                "name": "Hans Poorthuis",
                "email": None,
                "orcid": None,
                "external_id": "c0ab267a-ad56-480c-a13a-90b325f45b5d",
                "is_external": None,
            }
        ],
        "has_parts": [],
        "is_part_of": [],
        "keywords": [
            "correspondentie",
            "Didactiek",
            "eigenschappen",
            "macro",
            "macro-meso-micro",
            "meso",
            "micro",
            "scheikunde",
            "structuur"
        ],
        "score": 0.0,
        "provider": "Stimuleringsregeling Open en Online Onderwijs",
        "doi": None,
        "lom_educational_levels": [
            "HBO"
        ],
        "material_types": ["unknown"],
        "studies": [],
        "disciplines": [
            "exact_informatica"
        ],
        "ideas": [],
        "study_vocabulary": [
            "http://purl.edustandaard.nl/concept/128a7da4-7d5c-4625-8b16-fec02aa94f5d",
            "http://purl.edustandaard.nl/concept/43943d13-306a-4838-a9d4-6a3c4f7a8e11",
            "applied-science"
        ],
        "technical_type": "document",
        "publishers": [
            "Hogeschool Utrecht",
            "SURFnet"
        ],
        "consortium": "Stimuleringsregeling Open en Online Onderwijs",
        "subtitle": None
    }
    expected_product_count = 13  # 1 original, 15 copies and minus 3 deletes

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="supersurf")
        create_time = datetime(year=2000, month=1, day=1)
        delete_time = datetime(year=2024, month=1, day=1)
        # We duplicate the ProductDocument data a bunch to create larger responses
        product = ProductDocument.objects.first()
        identity = product.identity
        for ix in range(0, 15):
            product.id = None
            product.pk = None
            product.identity = f"{identity}-{ix}"
            if not ix % 5:
                product.state = ProductDocument.States.DELETED
                product.properties["state"] = ProductDocument.States.DELETED
                product.set_metadata(current_time=delete_time)
            else:
                product.state = ProductDocument.States.ACTIVE
                product.properties["state"] = ProductDocument.States.ACTIVE
                product.set_metadata(current_time=create_time)
            product.save()

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_list(self):
        list_url = reverse(self.list_view_name)
        response = self.client.get(list_url + "?page=1&page_size=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if not self.format:
            self.assertEqual(data["next"], "http://testserver/api/v1/product/?page=2&page_size=10")
        else:
            self.assertEqual(data["next"], f"http://testserver/api/v1/product/{self.format}/?page=2&page_size=10")
        self.assertIsNone(data["previous"])
        self.assertEqual(len(data["results"]), 10)
        self.assertEqual(data["count"], self.expected_product_count)

    def test_list_second_page(self):
        list_url = reverse(self.list_view_name)
        response = self.client.get(list_url + "?page=2&page_size=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if not self.format:
            self.assertEqual(data["previous"], "http://testserver/api/v1/product/?page_size=10")
        else:
            self.assertEqual(data["previous"], f"http://testserver/api/v1/product/{self.format}/?page_size=10")
        self.assertIsNone(data["next"])
        self.assertEqual(len(data["results"]), self.expected_product_count - 10)
        self.assertEqual(data["count"], self.expected_product_count)

    def test_list_no_dataset_version(self):
        DatasetVersion.objects.all().update(is_current=False)
        list_url = reverse(self.list_view_name)
        response = self.client.get(list_url + "?page=1&page_size=10")
        self.assertEqual(response.status_code, 417)
        data = response.json()
        self.assertEqual(data["detail"], "Missing a current dataset version to list data")

    def test_list_modified_since(self):
        for product in ProductDocument.objects.all().order_by("id")[:3]:
            product.metadata["modified_at"] = "2024-05-01T00:00:00"
            product.save()
        list_url = reverse(self.list_view_name)
        response = self.client.get(list_url + "?page=1&page_size=10&modified_since=2024-05-01T00:00:00")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNone(data["previous"])
        self.assertIsNone(data["next"])
        self.assertEqual(len(data["results"]), 3)
        self.assertEqual(
            len([rsl for rsl in data["results"] if rsl["state"] == "deleted"]), 1,
            "Expected modified_since parameter to expose deletes if they happened after the specified datetime"
        )
        self.assertEqual(data["count"], 3)

    def test_detail(self):
        detail_url = reverse(self.detail_view_name, args=("sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e",))
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
        self.assertEqual(data["detail"], "No ProductDocument matches the given query.")

    def test_detail_quoted_id(self):
        """
        This test checks whether Documents can be referenced with "/" or other URL characters in their reference.
        When making detail requests for such Documents the client should URL encode the "external_id"
        """
        document = ProductDocument.objects.get(identity="sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e")
        document.identity += "/1"
        document.save()
        detail_url = reverse(
            self.detail_view_name,
            args=("sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e%2F1",)
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
class TestResearchProductDocumentView(TestDocumentView):
    expected_document_output = {
        "srn": "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e",
        "set": "sharekit:edusources",
        "state": "active",
        "external_id": "63903863-6c93-4bda-b850-277f3c9ec00e",
        "entity": "products",
        "score": 0.0,
        "published_at": "2017-09-27",
        "modified_at": "2021-04-15",
        "url": "https://surfsharekit.nl/objectstore/88c687c8-fbc4-4d69-a27d-45d9f30d642b",
        "title": "Didactiek van macro-meso-micro denken bij scheikunde",
        "description": "Geen samenvatting",
        "language": "nl",
        "copyright": "cc-by-sa-40",
        "video": None,
        "harvest_source": "edusources",
        "previews": None,
        "files": [
            {
                "srn": "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e:"
                       "7ec8985621b50d7bf29b06cf4d413191d0a20bd4",
                "url": "https://surfsharekit.nl/objectstore/88c687c8-fbc4-4d69-a27d-45d9f30d642b",
                "hash": "7ec8985621b50d7bf29b06cf4d413191d0a20bd4",
                "type": "document",
                "state": "active",
                "title": "IMSCP_94812.zip",
                "is_link": False,
                "priority": 0,
                "copyright": "cc-by-sa-40",
                "mime_type": "application/x-zip",
                "access_rights": "OpenAccess",
                "video": None,
                "previews": None,
            },
            {
                "srn": "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e:"
                       "339df213a16895868ba4bfc635b7d3348348e33a",
                "url": "https://surfsharekit.nl/objectstore/9f71f782-09de-48b1-a10f-15d882471df7",
                "hash": "339df213a16895868ba4bfc635b7d3348348e33a",
                "type": "document",
                "state": "active",
                "title": "Didactiek van macro-meso-micro denken bij scheikunde.pdf",
                "is_link": False,
                "priority": 0,
                "copyright": "cc-by-sa-40",
                "mime_type": "application/pdf",
                "access_rights": "OpenAccess",
                "previews": {
                    "preview": "https://surfpol-harvester-content-prod.s3.amazonaws.com/thumbnails/files/previews/pdf/"
                               "20240219154612151932.9f71f782-09de-48b1-a10f-15d882471df7-thumbnail-400x300.png",
                    "full_size": "https://surfpol-harvester-content-prod.s3.amazonaws.com/files/previews/pdf/"
                                 "20240219154612151932.9f71f782-09de-48b1-a10f-15d882471df7.png",
                    "preview_small": "https://surfpol-harvester-content-prod.s3.amazonaws.com/thumbnails/files/"
                                     "previews/pdf/20240219154612151932.9f71f782-09de-48b1-a10f-15d882471df7"
                                     "-thumbnail-200x150.png"
                },
                "video": None,
            },
            {
                "srn": "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e:"
                       "ae362bbe89cae936c89aed50dfd6b7a1cb6bf03b",
                "url": "https://maken.wikiwijs.nl/94812/Macro_meso_micro#!page-2935729",
                "hash": "ae362bbe89cae936c89aed50dfd6b7a1cb6bf03b",
                "type": "website",
                "state": "active",
                "title": "URL 1",
                "is_link": True,
                "priority": 0,
                "copyright": "cc-by-sa-40",
                "mime_type": "text/html",
                "access_rights": "OpenAccess",
                "video": None,
                "previews": None,
            }
        ],
        "authors": [
            {
                "dai": None,
                "isni": None,
                "name": "Ruud Kok",
                "email": None,
                "orcid": None,
                "external_id": "83e7c163-075e-4eb2-8247-d975cf047dba",
                "is_external": None,
            },
            {
                "dai": None,
                "isni": None,
                "name": "Astrid Bulte",
                "email": None,
                "orcid": None,
                "external_id": "1174c1b9-f010-4a0a-98c0-2ceeefd0b506",
                "is_external": None,
            },
            {
                "dai": None,
                "isni": None,
                "name": "Hans Poorthuis",
                "email": None,
                "orcid": None,
                "external_id": "c0ab267a-ad56-480c-a13a-90b325f45b5d",
                "is_external": None,
            }
        ],
        "has_parts": [],
        "is_part_of": [],
        "keywords": [
            "correspondentie",
            "Didactiek",
            "eigenschappen",
            "macro",
            "macro-meso-micro",
            "meso",
            "micro",
            "scheikunde",
            "structuur"
        ],
        "provider": "Stimuleringsregeling Open en Online Onderwijs",
        "doi": None,
        "type": "document",
        "research_object_type": None,
        "parties": [
            "Hogeschool Utrecht",
            "SURFnet"
        ],
        "research_themes": [],
        "projects": [],
        "owners": [
            {
                "dai": None,
                "isni": None,
                "name": "Ruud Kok",
                "email": None,
                "orcid": None,
                "external_id": "83e7c163-075e-4eb2-8247-d975cf047dba",
                "is_external": None,
            }
        ],
        "contacts": [
            {
                "dai": None,
                "isni": None,
                "name": "Ruud Kok",
                "email": None,
                "orcid": None,
                "external_id": "83e7c163-075e-4eb2-8247-d975cf047dba",
                "is_external": None,
            }
        ],
        "subtitle": None
    }


class TestRawDocumentView(TestDocumentView):

    format = "raw"
    list_view_name = "v1:products:raw-products"
    detail_view_name = "v1:products:raw-product-detail"
    expected_document_output = {
        "id": 1,
        "created_at": "2024-04-18T01:01:46.829000Z",
        "modified_at": "2024-04-18T01:01:46.829000Z",
        "reference": None,
        "identity": "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e",
        "state": "active",
        "metadata": {
            "hash": "a867e8e5fb9639cb69596f59d70631a5a5551f7b",
            "language": "nl",
            "provider": "Stimuleringsregeling Open en Online Onderwijs",
            "created_at": "2024-04-17T14:19:12.720000Z",
            "deleted_at": None,
            "modified_at": "2024-04-17T14:19:12.720000Z"
        }
    }
    expected_product_count = 16  # 1 original and 15 copies including all deletes


class TestMetadataDocumentView(TestDocumentView):

    format = "metadata"
    list_view_name = "v1:products:metadata-products"
    detail_view_name = "v1:products:metadata-product-detail"
    expected_document_output = {
        "id": 1,
        "srn": "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e",
        "state": "active",
        "title": "Didactiek van macro-meso-micro denken bij scheikunde",
        "reference": "63903863-6c93-4bda-b850-277f3c9ec00e",
        "language": "nl",
        "created_at": "2024-04-17T14:19:12.720000Z",
        "modified_at": "2024-04-17T14:19:12.720000Z"
    }
