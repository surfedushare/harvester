from unittest.mock import patch
from datetime import timedelta
from time import sleep

from django.test import TestCase
from django.utils.timezone import now

from search.tests.mocks import get_search_client_mock
from search.models import OpenSearchIndex
from search.tasks import sync_opensearch_indices
from testing.constants import ENTITY_SEQUENCE_PROPERTIES
from testing.utils.generators import seed_generator
from testing.utils.factories import create_datatype_models
from testing.models import Dataset


class TestSyncOpenSearchIndices(TestCase):

    search_client = get_search_client_mock(has_history=True)

    start_time = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.start_time = now()
        sleep(1)  # create a little bit of a delta to ensure documents aren't excluded because of time restrictions
        # The inactive data shouldn't be indexed, because the Dataset indicates no indexing is required
        inactive_dataset, inactive_dataset_version, inactive_sets, inactive_documents = create_datatype_models(
            "testing", ["simple_set"],
            list(seed_generator("simple", 10, ENTITY_SEQUENCE_PROPERTIES["simple"], has_language=True)),
            5,
        )
        inactive_index = OpenSearchIndex.build("testing", "test", "0.0.1")
        inactive_index.pushed_at = cls.start_time
        inactive_index.save()
        inactive_dataset_version.index = inactive_index
        inactive_dataset_version.save()
        inactive_dataset.indexing = Dataset.IndexingOptions.NO
        inactive_dataset.save()
        # The historic data shouldn't be indexed, because we only index the most recent version
        historic_dataset, historic_dataset_version, historic_sets, historic_documents = create_datatype_models(
            "testing", ["simple_set"],
            list(seed_generator("simple", 10, ENTITY_SEQUENCE_PROPERTIES["simple"], has_language=True)),
            5
        )
        historic_index = OpenSearchIndex.build("testing", "test", "0.0.2")
        historic_index.pushed_at = cls.start_time
        historic_index.save()
        historic_dataset_version.index = historic_index
        historic_dataset_version.is_current = False
        historic_dataset_version.save()
        # Finally we create a set that should be indexed
        # However we only connect this data to an index in each test
        cls.dataset, cls.dataset_version, cls.sets, cls.documents = create_datatype_models(
            "testing", ["simple_set"],
            list(seed_generator("simple", 10, ENTITY_SEQUENCE_PROPERTIES["simple"], has_language=True)),
            10
        )

    def setUp(self):
        super().setUp()
        self.index = OpenSearchIndex.build("testing", "test", "0.0.3")
        self.index.pushed_at = self.start_time
        self.index.save()
        self.dataset_version.index = self.index
        self.dataset_version.save()

    @patch("search.models.index.get_opensearch_client", return_value=search_client)
    @patch("search.models.index.streaming_bulk")
    def test_sync_opensearch_indices(self, streaming_bulk_mock, get_search_client_mock):
        sync_opensearch_indices("testing")
        # Check if data was send to search engine
        self.assertEqual(streaming_bulk_mock.call_count, 3, "Expected a separate call for nl, en and unk")
        for args, kwargs in streaming_bulk_mock.call_args_list:
            client, docs = args
            alias, dataset_info = kwargs["index"].split("--")
            dataset, version, language = dataset_info.split("-")
            if language == "nl":
                self.assertEqual(len(docs), 3)
            elif language == "en":
                self.assertEqual(len(docs), 4)
            elif language == "unk":
                self.assertEqual(len(docs), 3)
            self.assertEqual(dataset, "test")
            self.assertEqual(version, "003", "Only expected one dataset version to get indexed")
        # Check that pushed_at was updated
        for index in OpenSearchIndex.objects.filter(name__contains="test-0.0.3"):
            self.assertGreater(index.pushed_at, self.start_time)
        for index in OpenSearchIndex.objects.exclude(name__contains="test-0.0.3"):
            self.assertEqual(index.pushed_at, self.start_time,
                             "Only the latest DatasetVersions of the newest Dataset should get pushed")

    @patch("search.models.index.get_opensearch_client", return_value=search_client)
    @patch("search.models.index.streaming_bulk")
    def test_sync_indices_new(self, streaming_bulk_mock, get_search_client_mock):
        the_future = self.start_time + timedelta(days=3)
        self.index.pushed_at = the_future
        self.index.save()
        sync_opensearch_indices("testing")
        self.assertEqual(streaming_bulk_mock.call_count, 0)
        # Check that pushed_at was not updated
        for index in OpenSearchIndex.objects.filter(name__contains="test-0.0.3"):
            self.assertEqual(index.pushed_at, the_future)
        for index in OpenSearchIndex.objects.exclude(name__contains="test-0.0.3"):
            self.assertEqual(index.pushed_at, self.start_time,
                             "Only the latest DatasetVersions of the newest Dataset should get pushed")
