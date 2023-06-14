from django.test import override_settings
from django.urls import reverse
from search_client import DocumentTypes
from search.tests.views.base import OpenSearchTestCaseMixin, DocumentAPITestCase


class TestStatsView(DocumentAPITestCase):

    def test_stats(self):
        stats_url = reverse("v1:search:search-stats")
        response = self.client.get(stats_url, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, {"documents": 2})


@override_settings(OPENSEARCH_ALIAS_PREFIX="test")
class TestLearningMaterialStatsView(OpenSearchTestCaseMixin, TestStatsView):
    document_type = DocumentTypes.LEARNING_MATERIAL


@override_settings(DOCUMENT_TYPE=DocumentTypes.RESEARCH_PRODUCT, OPENSEARCH_ALIAS_PREFIX="test")
class TestResearchProductStatsView(OpenSearchTestCaseMixin, TestStatsView):
    document_type = DocumentTypes.RESEARCH_PRODUCT
