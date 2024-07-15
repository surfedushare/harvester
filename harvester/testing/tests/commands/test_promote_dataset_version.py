from unittest.mock import patch

from django.test import TestCase, override_settings
from django.core.management import call_command, CommandError

from products.models import DatasetVersion as ProductDatasetVersion
from products.sources.sharekit import SEQUENCE_PROPERTIES
from search.models import OpenSearchIndex
from testing.utils.mocks import get_search_client_mock
from testing.utils.factories import create_datatype_models
from testing.utils.generators import seed_generator


class TestPromoteDatasetVersion(TestCase):

    search_client = get_search_client_mock(has_history=True)
    dataset_version = None

    @classmethod
    def setUpTestData(cls):
        product_seeds = seed_generator(
            "sharekit", 10,
            app_label="products", sequence_properties=SEQUENCE_PROPERTIES, has_language=True
        )
        product_seeds = list(product_seeds)
        active_dataset, active_dataset_version, active_sets, active_documents = create_datatype_models(
            "products", ["test"], product_seeds[0:5], 5
        )
        active_dataset_version.version = "0.0.1"
        active_dataset_version.index = OpenSearchIndex.build("products", "test", "0.0.1")
        active_dataset_version.index.save()
        active_dataset_version.save()
        cls.dataset_version = active_dataset_version

    def setUp(self):
        super().setUp()
        self.search_client.indices.put_alias.reset_mock()
        self.search_client.indices.create.reset_mock()
        self.search_client.indices.delete.reset_mock()
        ProductDatasetVersion.objects.all().update(is_current=False)

    def assert_index_promoted(self):
        # Indices should not get recreated
        self.assertEqual(self.search_client.indices.delete.call_count, 0)
        self.assertEqual(self.search_client.indices.create.call_count, 0)
        # Latest alias should update
        self.assertEqual(self.search_client.indices.put_alias.call_count, 6)
        for args, kwargs in self.search_client.indices.put_alias.call_args_list:
            content_key, identifier = kwargs["index"].split("--")
            project, entity = content_key.split("-")
            self.assertEqual(project, "edusources")
            self.assertEqual(entity, "products")
            version_name, version_number, language = identifier.split("-")
            self.assertEqual(version_name, "test")
            self.assertEqual(version_number, "001")
            self.assertIn(language, ["nl", "en", "unk"])
            self.assertIn(kwargs["name"], [
                "edusources-nl", "edusources-en", "edusources-unk",
                "edusources-products-nl", "edusources-products-en", "edusources-products-unk",
            ])

    def assert_is_current(self, expected_is_current):
        self.assertEqual(ProductDatasetVersion.objects.all().count(), 1,
                         "Promote index version should not create extra dataset versions")
        self.assertEqual(
            ProductDatasetVersion.objects.filter(is_current=expected_is_current).count(), 1,
            f"Expected the existing version to become/remain is_current={expected_is_current}, "
            "but asserted the opposite"
        )

    @override_settings(VERSION="0.0.1")
    @patch("search.models.index.get_opensearch_client", return_value=search_client)
    def test_promote_dataset(self, get_search_client):
        get_search_client.reset_mock()
        call_command("promote_dataset_version", "--dataset=test")
        self.assert_index_promoted()

        get_search_client.reset_mock()
        call_command("promote_dataset_version", "--dataset=test", "--harvester-version=0.0.1")
        self.assert_index_promoted()
        self.assert_is_current(True)

    @patch("search.models.index.get_opensearch_client", return_value=search_client)
    def test_promote_dataset_version(self, get_search_client):
        get_search_client.reset_mock()
        call_command("promote_dataset_version", f"--dataset-version={self.dataset_version.id}")
        self.assert_index_promoted()
        self.assert_is_current(True)

    def test_promote_invalid(self):
        try:
            call_command("promote_dataset_version")
            self.fail("Expected promote_dataset_version to fail with dataset and dataset_version unspecified")
        except CommandError:
            pass
        try:
            call_command("promote_dataset_version", "--dataset=test", "--harvester-version=0.0.2",
                         "--app-label=core")
            self.fail("Expected promote_dataset_version to fail with invalid harvester version specified")
        except CommandError:
            pass
        self.assert_is_current(False)
