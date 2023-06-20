from django.test import override_settings
from django.urls import reverse
from search_client import DocumentTypes
from search.tests.views.base import OpenSearchTestCaseMixin, DocumentAPITestCase


class TestSimilarityView(DocumentAPITestCase):

    def test_similarity(self):
        similarity_params = "?external_id=123&language=nl"
        similarity_url = reverse("v1:search:suggestions-similarity") + similarity_params
        response = self.client.get(similarity_url, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 4)
        self.assertEqual(data["results_total"], {"value": 4, "is_precise": True})
        self.assert_result_properties(data["results"][0])

    def test_not_found(self):
        similarity_params = "?external_id=does-not-exist&language=nl"
        similarity_url = reverse("v1:search:suggestions-similarity") + similarity_params
        response = self.client.get(similarity_url, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 0)
        self.assertEqual(data["results_total"], {"value": 0, "is_precise": True})


@override_settings(OPENSEARCH_ALIAS_PREFIX="test")
class TestLearningMaterialSimilarityView(OpenSearchTestCaseMixin, TestSimilarityView):
    document_type = DocumentTypes.LEARNING_MATERIAL

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.index_document(
            cls.document_type, external_id="def",
        )
        cls.index_document(
            cls.document_type, external_id="123",
        )
        cls.index_document(
            cls.document_type, is_last_document=True, external_id="456",
        )


@override_settings(DOCUMENT_TYPE=DocumentTypes.RESEARCH_PRODUCT, OPENSEARCH_ALIAS_PREFIX="test")
class TestResearchProductSimilarityView(OpenSearchTestCaseMixin, TestSimilarityView):
    document_type = DocumentTypes.RESEARCH_PRODUCT

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.index_document(
            cls.document_type, external_id="def",
        )
        cls.index_document(
            cls.document_type, external_id="123",
        )
        cls.index_document(
            cls.document_type, is_last_document=True, external_id="456",
        )


@override_settings(DOCUMENT_TYPE=DocumentTypes.RESEARCH_PRODUCT, OPENSEARCH_ALIAS_PREFIX="test")
class TestAuthorSimilarityView(OpenSearchTestCaseMixin, DocumentAPITestCase):

    document_type = DocumentTypes.RESEARCH_PRODUCT

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.index_document(
            cls.document_type, external_id="123", topic="biology", is_last_document=True
        )

    def test_author_similarity(self):
        similarity_params = "?author_name=Theo van den Bogaart"
        similarity_url = reverse("v1:search:suggestions-author") + similarity_params
        response = self.client.get(similarity_url, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results_total"], {"value": 1, "is_precise": True})
        self.assert_result_properties(data["results"][0])
        self.assertEqual(data["results"][0]["external_id"], "123")

    def test_not_found(self):
        similarity_params = "?author_name=Does Not Exist"
        similarity_url = reverse("v1:search:suggestions-author") + similarity_params
        response = self.client.get(similarity_url, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 0)
        self.assertEqual(data["results_total"], {"value": 0, "is_precise": True})
