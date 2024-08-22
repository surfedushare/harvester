from django.test import override_settings
from django.urls import reverse

from search_client.constants import Platforms, Entities
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
    platform = Platforms.EDUSOURCES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.index_document(Entities.PRODUCTS, external_id="def", source="surfsharekit")
        cls.index_document(Entities.PRODUCTS, external_id="123", source="surfsharekit")
        cls.index_document(Entities.PRODUCTS, is_last_entity_document=True, external_id="456", source="surfsharekit")


@override_settings(PLATFORM=Platforms.PUBLINOVA, OPENSEARCH_ALIAS_PREFIX="test")
class TestResearchProductSimilarityView(OpenSearchTestCaseMixin, TestSimilarityView):
    platform = Platforms.PUBLINOVA

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.index_document(Entities.PRODUCTS, external_id="def", source="surfsharekit")
        cls.index_document(Entities.PRODUCTS, external_id="123", source="surfsharekit")
        cls.index_document(Entities.PRODUCTS, is_last_entity_document=True, external_id="456", source="surfsharekit")


@override_settings(PLATFORM=Platforms.PUBLINOVA, OPENSEARCH_ALIAS_PREFIX="test")
class TestAuthorSimilarityView(OpenSearchTestCaseMixin, DocumentAPITestCase):

    platform = Platforms.PUBLINOVA

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.index_document(Entities.PRODUCTS, external_id="123", topic="biology", is_last_entity_document=True)

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
