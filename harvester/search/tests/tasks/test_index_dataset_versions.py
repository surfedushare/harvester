from unittest.mock import patch, ANY
from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now

from search.tests.mocks import get_search_client_mock
from search.models import OpenSearchIndex
from search.tasks import index_dataset_versions
from testing.constants import ENTITY_SEQUENCE_PROPERTIES
from testing.utils.generators import seed_generator
from testing.utils.factories import create_datatype_models
from testing.models import Dataset


class TestIndexDatasetVersions(TestCase):

    search_client = get_search_client_mock(has_history=True)
    start_time = None

    @classmethod
    def setUpTestData(cls):
        # Set start time, but create a little bit of a delta to ensure documents aren't excluded,
        # because of time restrictions
        cls.start_time = now() - timedelta(seconds=1)
        # Creating some fake data to index, but the actual OpenSearchIndex instances are created per test.
        cls.dataset, cls.dataset_version, cls.sets, cls.documents = create_datatype_models(
            "testing", ["simple_set"],
            list(seed_generator("simple", 10, ENTITY_SEQUENCE_PROPERTIES["simple"], has_language=True)),
            10
        )
        cls.deleted_document = cls.documents[0]
        cls.deleted_document.state = cls.deleted_document.States.DELETED
        cls.deleted_document.save()

    def setUp(self):
        super().setUp()
        self.index = OpenSearchIndex.build("testing", "test", "0.0.3")
        self.index.pushed_at = self.start_time
        self.index.save()
        self.dataset_version.dataset.indexing = Dataset.IndexingOptions.INDEX_AND_PROMOTE
        self.dataset_version.dataset.save()
        self.dataset_version.index = self.index
        self.dataset_version.save()
        self.search_client.indices.put_alias.reset_mock()
        self.search_client.indices.delete_alias.reset_mock()
        self.search_client.indices.create.reset_mock()
        self.search_client.indices.delete.reset_mock()

    def assert_document_stream(self, streaming_bulk_mock, exclude_deletes=False):
        self.assertEqual(streaming_bulk_mock.call_count, 4, "Expected a separate call for nl, en, unk and all")
        for args, kwargs in streaming_bulk_mock.call_args_list:
            client, docs = args
            alias, dataset_info = kwargs["index"].split("--")
            # Check language based call when appropriate and strip the language postfix
            if dataset_info.endswith("nl"):
                self.assertEqual(len(docs), 3)
                dataset_info = dataset_info[:-3]
            elif dataset_info.endswith("en"):
                expected_count = 3 if exclude_deletes else 4
                self.assertEqual(len(docs), expected_count)
                dataset_info = dataset_info[:-3]
            elif dataset_info.endswith("unk"):
                self.assertEqual(len(docs), 3)
                dataset_info = dataset_info[:-4]
            # Non-language asserts from here
            dataset, version = dataset_info.split("-")
            self.assertEqual(dataset, "test")
            self.assertEqual(version, "003", "Only expected one dataset version to get indexed")

    def assert_alias_deletion(self, platform: str, entity: str, languages: list[str]):
        for language in languages:
            self.search_client.indices.delete_alias.assert_any_call(
                index=f"{platform}-{entity}--*-*-{language}",
                name=f"{platform}-{entity}-{language}"
            )
            self.search_client.indices.delete_alias.assert_any_call(
                index=f"{platform}-{entity}--*-*-{language}",
                name=f"{platform}-{language}"
            )
            self.search_client.indices.delete_alias.assert_any_call(
                index=f"*-*-*-{platform}-{language}",
                name=f"{platform}-{language}"
            )
            self.search_client.indices.delete_alias.assert_any_call(
                index=f"{platform}-{entity}--*-*",
                name=f"{platform}-{entity}"
            )

    def assert_alias_creation(self, platform: str, entity: str, languages: list[str]):
        for language in languages:
            self.search_client.indices.put_alias.assert_any_call(
                index=f"{platform}-{entity}--test-003",
                name=f"{platform}-{entity}"
            )
            self.search_client.indices.put_alias.assert_any_call(
                index=f"{platform}-{entity}--test-003-{language}",
                name=f"{platform}-{language}"
            )

    def assert_index_deletion(self, platform: str, entity: str, languages: list[str]):
        for language in languages:
            self.search_client.indices.delete.assert_any_call(
                index=f"{platform}-{entity}--test-003-{language}"
            )

    def assert_index_creation(self, platform: str, entity: str, languages: list[str]):
        for language in languages:
            self.search_client.indices.create.assert_any_call(
                index=f"{platform}-{entity}--test-003-{language}",
                body=ANY
            )

    @patch("search.models.index.get_opensearch_client", return_value=search_client)
    @patch("search.models.index.streaming_bulk")
    def test_index_promote(self, streaming_bulk_mock, get_search_client_mock):
        index_dataset_versions([("testing.DatasetVersion", self.dataset_version.id,)])
        # Check if data was sent to search engine
        self.assert_document_stream(streaming_bulk_mock)
        # Check DatasetVersion and OpensearchIndex updates
        self.dataset_version.refresh_from_db()
        self.assertTrue(self.dataset_version.is_index_promoted, "Expected DatasetVersion to be marked promoted.")
        self.dataset_version.index.refresh_from_db()
        self.assertGreater(self.dataset_version.index.pushed_at, self.start_time)
        # Check alias modifications
        self.assert_alias_deletion("edusources", "testing", ["en", "nl", "unk"])
        self.assert_alias_creation("edusources", "testing", ["en", "nl", "unk"])
        # Check indices are left alone
        self.assertEqual(self.search_client.indices.delete.call_count, 0, "Expected index not to be recreated")
        self.assertEqual(self.search_client.indices.create.call_count, 0, "Expected index not to be recreated")

    @patch("search.models.index.get_opensearch_client", return_value=search_client)
    @patch("search.models.index.streaming_bulk")
    def test_index_no_promote(self, streaming_bulk_mock, get_search_client_mock):
        self.dataset_version.dataset.indexing = Dataset.IndexingOptions.INDEX_ONLY
        self.dataset_version.dataset.save()

        index_dataset_versions([("testing.DatasetVersion", self.dataset_version.id,)])

        # Check if data was sent to search engine
        self.assert_document_stream(streaming_bulk_mock)
        # Check DatasetVersion and OpensearchIndex updates
        self.dataset_version.refresh_from_db()
        self.assertFalse(self.dataset_version.is_index_promoted, "Expected DatasetVersion to be not promoted.")
        self.dataset_version.index.refresh_from_db()
        self.assertGreater(self.dataset_version.index.pushed_at, self.start_time)
        # Check aliases are unchanged
        self.assertEqual(
            self.search_client.indices.delete_alias.call_count, 0,
            "Non promoted DatasetVersion shouldn't delete aliases"
        )
        self.assertEqual(
            self.search_client.indices.put_alias.call_count, 0,
            "Non promoted DatasetVersion shouldn't add aliases"
        )

    @patch("search.models.index.get_opensearch_client", return_value=search_client)
    @patch("search.models.index.streaming_bulk")
    def test_missing_dataset_version_index(self, streaming_bulk_mock, get_search_client_mock):
        index = self.dataset_version.index
        self.dataset_version.index = None
        self.dataset_version.save()

        index_dataset_versions([("testing.DatasetVersion", self.dataset_version.id,)])

        # Check documents aren't pushed
        self.assertEqual(streaming_bulk_mock.call_count, 0, "Expected no documents to get added without an index")
        # Check DatasetVersion and OpensearchIndex updates
        self.dataset_version.refresh_from_db()
        self.assertFalse(self.dataset_version.is_index_promoted, "Expected DatasetVersion to be not promoted.")
        index.refresh_from_db()
        self.assertEqual(index.pushed_at, self.start_time)
        # Check aliases are unchanged
        self.assertEqual(
            self.search_client.indices.delete_alias.call_count, 0,
            "Non promoted DatasetVersion shouldn't delete aliases"
        )
        self.assertEqual(
            self.search_client.indices.put_alias.call_count, 0,
            "Non promoted DatasetVersion shouldn't add aliases"
        )

    @patch("search.models.index.get_opensearch_client", return_value=search_client)
    @patch("search.models.index.streaming_bulk")
    def test_index_recreate(self, streaming_bulk_mock, get_search_client_mock):
        index_dataset_versions([("testing.DatasetVersion", self.dataset_version.id,)], recreate_indices=True)
        # Check if data was sent to search engine
        self.assert_document_stream(streaming_bulk_mock, exclude_deletes=True)
        # Check DatasetVersion and OpensearchIndex updates
        self.dataset_version.refresh_from_db()
        self.assertTrue(self.dataset_version.is_index_promoted, "Expected DatasetVersion to be marked promoted.")
        self.dataset_version.index.refresh_from_db()
        self.assertGreater(self.dataset_version.index.pushed_at, self.start_time)
        # Check alias modifications
        self.assert_alias_deletion("edusources", "testing", ["en", "nl", "unk"])
        self.assert_alias_creation("edusources", "testing", ["en", "nl", "unk"])
        # Check index recreation
        self.assert_index_deletion("edusources", "testing", ["en", "nl", "unk"])
        self.assert_index_creation("edusources", "testing", ["en", "nl", "unk"])
