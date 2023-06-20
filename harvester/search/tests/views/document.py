from django.test import override_settings
from django.urls import reverse
from search_client import DocumentTypes
from search.tests.views.base import OpenSearchTestCaseMixin, DocumentAPITestCase


class TestDocumentSearchView(DocumentAPITestCase):

    def test_search_all(self):
        search_url = reverse("v1:search:search-documents")
        post_data = {
            "search_text": "",
            "page": 1,
            "page_size": 10
        }
        response = self.client.post(search_url, data=post_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 2)
        self.assert_result_properties(data["results"][0])
        self.assertEqual(data["results_total"], {"value": 2, "is_precise": True})
        self.assertEqual(data["did_you_mean"], {})
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 10)
        self.assertIsNone(data["filter_counts"])

    def test_search_specific(self):
        search_url = reverse("v1:search:search-documents")
        post_data = {
            "search_text": "Nog een",
            "page": 1,
            "page_size": 10
        }
        response = self.client.post(search_url, data=post_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assert_result_properties(data["results"][0])
        self.assertEqual(data["results_total"], {"value": 1, "is_precise": True})
        self.assertEqual(data["did_you_mean"], {})
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 10)
        self.assertIsNone(data["filter_counts"])

    def test_search_not_found(self):
        search_url = reverse("v1:search:search-documents")
        post_data = {
            "search_text": "didatiek",
            "page": 1,
            "page_size": 10
        }
        response = self.client.post(search_url, data=post_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 0)
        self.assertEqual(data["results_total"], {"value": 0, "is_precise": True})
        self.assertEqual(data["did_you_mean"], {
            "original": "didatiek",
            "suggestion": "didactiek"
        })
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 10)
        self.assertIsNone(data["filter_counts"])


@override_settings(OPENSEARCH_ALIAS_PREFIX="test")
class TestLearningMaterialSearchView(OpenSearchTestCaseMixin, TestDocumentSearchView):

    fixtures = ["initial-metadata-edusources"]
    document_type = DocumentTypes.LEARNING_MATERIAL

    def test_search_including_filter_counts(self):
        search_url = reverse("v1:search:search-documents") + "?include_filter_counts=1"
        post_data = {
            "search_text": "",
            "page": 1,
            "page_size": 10,
            "filters": [
                {
                    "external_id": "learning_material_disciplines_normalized",
                    "items": ["exact_informatica"]
                }
            ]
        }
        response = self.client.post(search_url, data=post_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 2)
        self.assert_result_properties(data["results"][0])
        self.assertEqual(data["results_total"], {"value": 2, "is_precise": True})
        self.assertEqual(data["did_you_mean"], {})
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 10)
        self.assertEqual(data["filter_counts"], {
            "publishers.keyword-Wikiwijs Maken": 2,
            "learning_material_disciplines-exact_informatica": 2,
            "technical_type-document": 2,
            "learning_material_disciplines_normalized-exact_informatica": 2,
            "lom_educational_levels-HBO": 2,
            "language.keyword-nl": 2,
            "harvest_source-wikiwijsmaken": 2,
            "authors.name.keyword-Marc de Graaf": 2,
            "authors.name.keyword-Michel van Ast": 2,
            "authors.name.keyword-Theo van den Bogaart": 2,
            "studies-7afbb7a6-c29b-425c-9c59-6f79c845f5f0": 2,
            "copyright.keyword-cc-by-30": 2
        })

    def test_search_filter_does_not_exist(self):
        search_url = reverse("v1:search:search-documents") + "?include_filter_counts=1"
        post_data = {
            "search_text": "",
            "page": 1,
            "page_size": 10,
            "filters": [
                {
                    "external_id": "learning_material",
                    "items": ["does-not-exist"]
                }
            ]
        }
        response = self.client.post(search_url, data=post_data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data, {
            "filters": [
                "Invalid external_id for metadata field in filter 'learning_material'"
            ]
        })


@override_settings(DOCUMENT_TYPE=DocumentTypes.RESEARCH_PRODUCT, OPENSEARCH_ALIAS_PREFIX="test")
class TestResearchProductSearchView(OpenSearchTestCaseMixin, TestDocumentSearchView):
    document_type = DocumentTypes.RESEARCH_PRODUCT


class TestDocumentFindView(DocumentAPITestCase):

    def test_find(self):
        search_url = reverse("v1:search:find-document-detail", args=("3522b79c-928c-4249-a7f7-d2bcb3077f10",))
        response = self.client.get(search_url, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assert_result_properties(data)

    def test_not_found(self):
        search_url = reverse("v1:search:find-document-detail", args=("does-not-exist",))
        response = self.client.get(search_url, content_type="application/json")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["detail"], "Not found.")


@override_settings(OPENSEARCH_ALIAS_PREFIX="test")
class TestLearningMaterialFindView(OpenSearchTestCaseMixin, TestDocumentFindView):
    document_type = DocumentTypes.LEARNING_MATERIAL


@override_settings(DOCUMENT_TYPE=DocumentTypes.RESEARCH_PRODUCT, OPENSEARCH_ALIAS_PREFIX="test")
class TestResearchProductFindView(OpenSearchTestCaseMixin, TestDocumentFindView):
    document_type = DocumentTypes.RESEARCH_PRODUCT


class TestDocumentsFindView(DocumentAPITestCase):

    def test_find(self):
        search_url = reverse("v1:search:find-document-details")
        post_data = {
            "external_ids": [
                "3522b79c-928c-4249-a7f7-d2bcb3077f10",
                "abc",
                "def"  # does not exist
            ]
        }
        response = self.client.post(search_url, data=post_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 2)
        self.assertEqual(data["results_total"], {"value": 2, "is_precise": True})
        self.assert_result_properties(data["results"][0])

    def test_not_found(self):
        search_url = reverse("v1:search:find-document-details")
        post_data = {
            "external_ids": [
                "def"  # does not exist
            ]
        }
        response = self.client.post(search_url, data=post_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 0)
        self.assertEqual(data["results_total"], {"value": 0, "is_precise": True})


@override_settings(OPENSEARCH_ALIAS_PREFIX="test")
class TestLearningMaterialsFindView(OpenSearchTestCaseMixin, TestDocumentsFindView):
    document_type = DocumentTypes.LEARNING_MATERIAL


@override_settings(DOCUMENT_TYPE=DocumentTypes.RESEARCH_PRODUCT, OPENSEARCH_ALIAS_PREFIX="test")
class TestResearchProductsFindView(OpenSearchTestCaseMixin, TestDocumentsFindView):
    document_type = DocumentTypes.RESEARCH_PRODUCT
