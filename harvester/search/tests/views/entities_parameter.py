from django.test import override_settings
from django.urls import reverse

from search_client.constants import Platforms
from search.tests.views.base import OpenSearchTestCaseMixin, DocumentAPITestCase


class TestProductSearchView(DocumentAPITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.entity_status_code_expectations = {
            "products:default": 200,
            "products": 200,
            "products:unavailable": 400,
            "unknown:default": 400,
            "unknown": 400,
        }

    def test_search(self):
        search_url = reverse("v1:search:search-documents")
        post_data = {
            "search_text": "",
            "page": 1,
            "page_size": 10
        }
        for entity, expected_status_code in self.entity_status_code_expectations.items():
            url = f"{search_url}?entities={entity}"
            response = self.client.post(url, data=post_data, content_type="application/json")
            self.assertEqual(response.status_code, expected_status_code)

    def test_find(self):
        find_url = reverse(
            "v1:search:find-document-detail",
            args=("sharekit:edusources:3522b79c-928c-4249-a7f7-d2bcb3077f10",)
        )
        for entity, expected_status_code in self.entity_status_code_expectations.items():
            url = f"{find_url}?entities={entity}"
            response = self.client.get(url, content_type="application/json")
            self.assertEqual(response.status_code, expected_status_code)

    def test_multiple_find(self):
        multiple_find_url = reverse("v1:search:find-document-details")
        post_data = {
            "srns": [
                "sharekit:edusources:3522b79c-928c-4249-a7f7-d2bcb3077f10"
            ]
        }
        for entity, expected_status_code in self.entity_status_code_expectations.items():
            url = f"{multiple_find_url}?entities={entity}"
            response = self.client.post(url, data=post_data, content_type="application/json")
            self.assertEqual(response.status_code, expected_status_code)

    def test_autocomplete(self):
        autocomplete_url = reverse("v1:search:search-autocomplete")
        for entity, expected_status_code in self.entity_status_code_expectations.items():
            url = f"{autocomplete_url}?query=did&entities={entity}"
            response = self.client.get(url, content_type="application/json")
            self.assertEqual(response.status_code, expected_status_code)

    def test_similarity(self):
        srn = "sharekit:edusources:3522b79c-928c-4249-a7f7-d2bcb3077f10"
        similarity_url = reverse("v1:search:suggestions-similarity")
        for entity, expected_status_code in self.entity_status_code_expectations.items():
            url = f"{similarity_url}?srn={srn}&language=nl&entities={entity}"
            response = self.client.get(url, content_type="application/json")
            self.assertEqual(response.status_code, expected_status_code)

    def test_stats(self):
        stats_url = reverse("v1:search:search-stats")

        for entity, expected_status_code in self.entity_status_code_expectations.items():
            url = f"{stats_url}?entities={entity}"
            response = self.client.get(url, content_type="application/json")
            self.assertEqual(response.status_code, expected_status_code)
            if response.status_code == 200:
                data = response.json()
                self.assertEqual(data, {"documents": 2, "products": 2})


@override_settings(OPENSEARCH_ALIAS_PREFIX="test")
class TestEdusourcesProductSearchViews(OpenSearchTestCaseMixin, TestProductSearchView):
    platform = Platforms.EDUSOURCES
    presets = ["products:default"]


@override_settings(PLATFORM=Platforms.PUBLINOVA, OPENSEARCH_ALIAS_PREFIX="test")
class TestPublinovaProductSearchViews(OpenSearchTestCaseMixin, TestProductSearchView):
    platform = Platforms.PUBLINOVA
    presets = ["products:default"]

    def test_author_similarity(self):
        author = "Theo van den Bogaart"
        similarity_url = reverse("v1:search:suggestions-author")
        for entity, expected_status_code in self.entity_status_code_expectations.items():
            url = f"{similarity_url}?author_name={author}&entities={entity}"
            response = self.client.get(url, content_type="application/json")
            self.assertEqual(response.status_code, expected_status_code)
