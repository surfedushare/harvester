from django.test import TestCase
from django.utils.timezone import now
from django.contrib.auth.models import User

from core.analysis.matomo import create_or_update_download_query_rankings
from core.tests.factories import create_dataset_version, DatasetFactory, DocumentFactory
from core.tests.factories.matomo import MatomoVisitsResourceFactory
from core.models import Query, QueryRanking, DatasetVersion


class TestCreateOrUpdateDownloadQueryRankings(TestCase):

    dataset_version = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        dataset = DatasetFactory.create()
        create_dataset_version(dataset=dataset, version="0.0.1", created_at=now(), include_current=True)
        dataset_version = DatasetVersion.objects.get_current_version()
        DocumentFactory.create(dataset_version=dataset_version,
                               reference="WikiwijsDelen:urn:uuid:d622776b-84be-45ee-bb0a-ae2c3e56bf59", language="nl")
        DocumentFactory.create(dataset_version=dataset_version,
                               reference="WikiwijsDelen:urn:uuid:a213da49-0658-4448-b418-4598311a1205", language="en")
        DocumentFactory.create(dataset_version=dataset_version,
                               reference="WikiwijsDelen:urn:uuid:fa88b25c-a00c-4afe-b198-3b33e9cc109a", language="nl")
        MatomoVisitsResourceFactory.create(is_initial=True)
        User.objects.create(username="supersurf")

    def test_create_or_update_download_query_rankings(self):
        create_or_update_download_query_rankings()
        self.assertEqual(Query.objects.count(), 1)
        query = Query.objects.last()
        self.assertEqual(query.query, '"fase"')
        self.assertEqual(QueryRanking.objects.count(), 1)
        query_ranking = QueryRanking.objects.last()
        self.assertEqual(query_ranking.query_id, query.id)
        self.assertEqual(query_ranking.ranking, {
            "edusources-nl:WikiwijsDelen:urn:uuid:d622776b-84be-45ee-bb0a-ae2c3e56bf59": 1
        })
