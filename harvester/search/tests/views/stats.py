from django.test import override_settings
from django.urls import reverse
from search_client.constants import Platforms
from search.tests.views.base import OpenSearchTestCaseMixin, DocumentAPITestCase


class TestStatsView(DocumentAPITestCase):

    def test_stats(self):
        stats_url = reverse("v1:search:search-stats")
        response = self.client.get(stats_url, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, {"documents": 2, "products": None, "projects": None})


@override_settings(OPENSEARCH_ALIAS_PREFIX="test")
class TestLearningMaterialStatsView(OpenSearchTestCaseMixin, TestStatsView):
    platform = Platforms.EDUSOURCES


@override_settings(PLATFORM=Platforms.PUBLINOVA, OPENSEARCH_ALIAS_PREFIX="test")
class TestResearchProductStatsView(OpenSearchTestCaseMixin, TestStatsView):
    platform = Platforms.PUBLINOVA
