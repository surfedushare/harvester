from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils.timezone import now

from search.models import OpenSearchIndex
from search.tests.mocks import get_search_client_mock


class TestOpenSearchIndexModel(TestCase):

    search_client = get_search_client_mock(has_history=True)

    def setUp(self):
        super().setUp()
        self.search_client.indices.create.reset_mock()
        self.search_client.indices.delete.reset_mock()

    def test_build(self):
        instance = OpenSearchIndex.build("testing", "test", "0.0.1")
        self.assertIsNone(instance.id)
        self.assertEqual(instance.name, "edusources-testing--test-0.0.1")
        self.assertEqual(instance.entity, "testing")
        self.assertEqual(set(instance.configuration.keys()), {"nl", "en", "unk", "all"})

    @patch("search.models.index.get_opensearch_client", return_value=search_client)
    def test_delete(self, get_search_client_mock):
        instance = OpenSearchIndex.build("testing", "test", "0.0.1")
        instance.save()
        instance.delete()  # we're testing this
        for language in ["en", "nl", "unk"]:
            self.search_client.indices.delete.assert_any_call(index=f"edusources-testing--test-001-{language}")
        self.search_client.indices.delete.assert_any_call(index="edusources-testing--test-001")

    @override_settings(OPENSEARCH_STRICT_MULTILINGUAL_FIELDS=False)
    def test_get_remote_names(self):
        instance = OpenSearchIndex.build("testing", "test", "0.0.1")
        instance.save()
        names = instance.get_remote_names()
        self.assertEqual(set(names), {
            "edusources-testing--test-001-en",
            "edusources-testing--test-001-nl",
            "edusources-testing--test-001-unk",
            "edusources-testing--test-001",
        })

    @patch("search.models.index.get_opensearch_client", return_value=search_client)
    def test_prepare_push(self, get_search_client_mock):
        # Setup some test data
        current_time = now()
        old_instance = OpenSearchIndex.build("testing", "test", "0.0.1")
        old_instance.pushed_at = current_time
        old_instance.clean()
        old_instance.save()
        # Create a new instance with identical version that should see the pushed_at of the old version
        instance = OpenSearchIndex.build("testing", "test", "0.0.1")
        instance.clean()
        instance.save()
        instance.prepare_push()
        self.assertEqual(instance.pushed_at, current_time)

    @patch("search.models.index.get_opensearch_client", return_value=search_client)
    def test_prepare_push_recreate(self, get_search_client_mock):
        # Setup some test data
        current_time = now()
        old_instance = OpenSearchIndex.build("testing", "test", "0.0.1")
        old_instance.pushed_at = current_time
        old_instance.clean()
        old_instance.save()
        # Create a new instance with identical version that should not see the pushed_at of the old version,
        # because we're testing the recreate case
        instance = OpenSearchIndex.build("testing", "test", "0.0.1")
        instance.clean()
        instance.save()
        instance.prepare_push(recreate=True)
        self.assertIsNone(instance.pushed_at)
