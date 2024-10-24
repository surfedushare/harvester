from django.test import override_settings
from django.urls import reverse
from search_client.constants import Platforms
from search.tests.views.base import OpenSearchTestCaseMixin, DocumentAPITestCase


class TestAutoCompleteView(DocumentAPITestCase):

    def test_autocomplete(self):
        autocomplete_url = reverse("v1:search:search-autocomplete") + "?query=did"
        response = self.client.get(autocomplete_url, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, ["didactiek"])

    def test_not_found(self):
        search_url = reverse("v1:search:search-autocomplete") + "?query=didat"
        response = self.client.get(search_url, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, [])


@override_settings(OPENSEARCH_ALIAS_PREFIX="test")
class TestLearningMaterialAutoCompleteView(OpenSearchTestCaseMixin, TestAutoCompleteView):
    platform = Platforms.EDUSOURCES


@override_settings(PLATFORM=Platforms.PUBLINOVA, OPENSEARCH_ALIAS_PREFIX="test")
class TestResearchProductAutoCompleteView(OpenSearchTestCaseMixin, TestAutoCompleteView):
    platform = Platforms.PUBLINOVA
