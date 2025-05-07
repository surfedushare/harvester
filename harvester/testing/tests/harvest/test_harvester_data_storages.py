from django.test import TestCase
from django.apps import apps

from core.loading import HarvesterDataStorages
from core.models.harvest import HarvestState
from core.models.pipeline import BatchBase, ProcessResultBase
from core.models.datatypes.set import HarvestSet
from core.models.datatypes.dataset import HarvestDataset
from core.models.datatypes.overwrite import HarvestOverwrite


class TestHarvesterDataStorages(TestCase):
    def setUp(self):
        self.model_label = "testing.TestDocument"  # Using the testing app for demonstration
        self.storages = HarvesterDataStorages.from_label(self.model_label)

    def test_basic_models_loaded(self):
        """
        Test that basic DataStorages models are properly loaded
        """
        self.assertIsNotNone(self.storages.model)
        self.assertIsNotNone(self.storages.DatasetVersion)
        self.assertIsNotNone(self.storages.Collection)
        self.assertIsNotNone(self.storages.Document)

    def test_harvester_models_loaded(self):
        """
        Test that harvester-specific models are properly loaded
        """
        self.assertIsNotNone(self.storages.Set)
        self.assertIsNotNone(self.storages.Dataset)
        self.assertIsNotNone(self.storages.HarvestState)
        self.assertIsNotNone(self.storages.Batch)
        self.assertIsNotNone(self.storages.ProcessResult)
        self.assertIsNotNone(self.storages.Overwrite)
        self.assertTrue(issubclass(self.storages.Set, HarvestSet))
        self.assertTrue(issubclass(self.storages.Dataset, HarvestDataset))
        self.assertTrue(issubclass(self.storages.HarvestState, HarvestState))
        self.assertTrue(issubclass(self.storages.Batch, BatchBase))
        self.assertTrue(issubclass(self.storages.ProcessResult, ProcessResultBase))
        self.assertTrue(issubclass(self.storages.Overwrite, HarvestOverwrite))


    def test_missing_optional_model(self):
        """
        Test that missing optional models are handled gracefully
        """
        # Create a test app label that doesn't have the Overwrite model
        test_model_label = "projects.ProjectDocument"
        storages = HarvesterDataStorages.from_label(test_model_label)

        # Required models should still be present
        self.assertIsNotNone(storages.Set, "Expected required model Set to be loaded.")
        self.assertIsNotNone(storages.Dataset, "Expected required model Dataset to be loaded.")
        self.assertIsNotNone(storages.HarvestState, "Expected required model HarvestState to be loaded.")
        self.assertIsNotNone(storages.Batch, "Expected required model Batch to be loaded.")
        self.assertIsNotNone(storages.ProcessResult, "Expected required model ProcessResult to be loaded.")
        # Optional Overwrite model should be None
        self.assertIsNone(storages.Overwrite, "Expected Overwrite to not be present for projects.")
