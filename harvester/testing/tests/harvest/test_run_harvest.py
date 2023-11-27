from unittest.mock import patch, call

from django.core.management import call_command
from django.test import TestCase

from testing.utils.factories import create_datatype_models
from testing.utils.generators import seed_generator


INITIAL_DATASET_VERSION_NATURAL_KEYS = [("files.datasetversion", 1), ("products.datasetversion", 1)]
DELTA_DATASET_VERSION_NATURAL_KEYS = [("files.datasetversion", 2), ("products.datasetversion", 2)]


class TestRunHarvest(TestCase):

    @patch("harvester.management.commands.run_harvest.index_dataset_versions")
    @patch("harvester.management.commands.run_harvest.dataset_versions_are_ready", return_value=False)
    @patch(
        "harvester.management.commands.run_harvest.harvest_entities",
        return_value=INITIAL_DATASET_VERSION_NATURAL_KEYS
    )
    def test_run_harvest_timeout_failure(self, harvest_entities_mock, dataset_versions_are_ready_mock,
                                         index_dataset_versions_mock):
        with self.assertRaises(ValueError):
            call_command("run_harvest", "--timeout=1", "--wait-interval=1", "--asynchronous")
        self.assertEqual(harvest_entities_mock.call_args_list, [call(reset=False, asynchronous=True)])
        self.assertEqual(index_dataset_versions_mock.call_count, 0, "Expected no indexation with only corrupt data")

    @patch("harvester.management.commands.run_harvest.index_dataset_versions")
    @patch("harvester.management.commands.run_harvest.dataset_versions_are_ready", return_value=False)
    @patch(
        "harvester.management.commands.run_harvest.harvest_entities",
        return_value=DELTA_DATASET_VERSION_NATURAL_KEYS
    )
    def test_run_harvest_timeout_fallback(self, harvest_entities_mock, dataset_versions_are_ready_mock,
                                          index_dataset_versions_mock):
        # Create the fallback data
        product_seeds = list(seed_generator("sharekit", 20, app_label="products"))
        product_dataset, product_version, product_sets, product_docs = create_datatype_models(
            "products", ["edusources"], product_seeds, len(product_seeds)
        )
        file_seeds = list(seed_generator("sharekit", 20, app_label="files"))
        file_dataset, file_version, file_sets, file_docs = create_datatype_models(
            "files", ["edusources"], file_seeds, len(file_seeds)
        )
        # Run command
        call_command("run_harvest", "--timeout=1", "--wait-interval=1", "--asynchronous")
        self.assertEqual(harvest_entities_mock.call_args_list, [call(reset=False, asynchronous=True)])
        self.assertEqual(
            index_dataset_versions_mock.call_args_list,
            [call([("files.datasetversion", file_version.id), ("products.datasetversion", product_version.id)])],
            "Expected command timeout to lead to use of fallback versions when available"
        )
