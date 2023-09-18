from unittest.mock import patch
from copy import copy

from django.test import TestCase
from django.utils.timezone import now

from datagrowth.configuration import register_defaults

from core.tasks.harvest.source import harvest_source
from sources.models.harvest import HarvestEntity
from files.tests.factories.tika import HttpTikaResourceFactory
from testing.constants import ENTITY_SEQUENCE_PROPERTIES
from testing.utils.generators import seed_generator, document_generator
from testing.utils.factories import create_datatype_models
from testing.models import Dataset, DatasetVersion, HarvestState, Set


class TestInitialHarvestSource(TestCase):

    fixtures = ["test-sources-harvest-models"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        register_defaults("global", {
            "cache_only": True
        })

    @classmethod
    def tearDownClass(cls):
        register_defaults("global", {
            "cache_only": False
        })
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.harvest_entity = HarvestEntity.objects.get(source__module="simple")
        self.dataset = Dataset.objects.create(
            name="test",
            is_harvested=True,
            indexing=Dataset.IndexingOptions.INDEX_AND_PROMOTE
        )
        self.dataset_version = DatasetVersion.objects.create(dataset=self.dataset)
        self.set = Set.objects.create(
            name="simple",
            pending_at=None,  # HarvestSet does not become pending until all data from source has been pulled
            identifier="srn",
            dataset_version=self.dataset_version
        )
        self.state = HarvestState.objects.create(
            dataset=self.dataset,
            harvest_set=self.set,
            entity=self.harvest_entity,
            set_specification="simple_set"
        )
        self.sequence_properties = copy(ENTITY_SEQUENCE_PROPERTIES["simple"])
        for seed in seed_generator("simple", 20, self.sequence_properties):
            HttpTikaResourceFactory.create(url=seed["url"])

    def test_harvest_source(self):
        seeding_patch_target = "core.tasks.harvest.source.HttpSeedingProcessor.__call__"
        seeding_patch_value = document_generator("simple", 20, 10, self.set, self.sequence_properties)
        with patch(seeding_patch_target, return_value=seeding_patch_value) as seeding_processor_call:
            harvest_source("testing", "simple", "simple_set", asynchronous=False)
        # Assert call to seeder
        seeding_processor_call.assert_called_with("simple_set", "1970-01-01T00:00:00Z")
        # Assert document state
        self.assertEqual(self.set.documents.count(), 20, "Expected 20 documents to get added")
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 0,
            "Expected no pending documents"
        )
        for ix, doc in enumerate(self.set.documents.all().order_by("created_at")):
            self.assertEqual(list(doc.pipeline.keys()), ["tika"])
            self.assertTrue(doc.pipeline["tika"]["success"])
            self.assertEqual(list(doc.derivatives.keys()), ["tika"])
            self.assertEqual(doc.derivatives["tika"], {
                "texts": [f"Tika content for http://localhost:8888/file/{ix}"]
            })
        # Assert Set state
        set_instance = Set.objects.get(id=self.set.id)
        self.assertIsNone(set_instance.pending_at)
        self.assertEqual(list(set_instance.pipeline.keys()), ["check_set_integrity"])
        self.assertTrue(set_instance.pipeline["check_set_integrity"]["success"])
        # Assert DatasetVersion state
        dataset_version = DatasetVersion.objects.get(id=self.dataset_version.id)
        self.assertIsNone(dataset_version.pending_at)
        self.assertEqual(
            list(dataset_version.pipeline.keys()),
            ["create_opensearch_index", "set_current_dataset_version"]
        )
        self.assertTrue(dataset_version.pipeline["create_opensearch_index"]["success"])
        self.assertIsNotNone(dataset_version.index)


class TestDeltaHarvestSource(TestCase):

    fixtures = ["test-sources-harvest-models"]

    def setUp(self) -> None:
        super().setUp()
        self.current_time = now()
        self.sequence_properties = ENTITY_SEQUENCE_PROPERTIES["simple"]
        self.set_names = ["simple:simple_set", "merge:merge_set"]
        self.seeds = list(seed_generator("simple", 100, self.sequence_properties))
        self.dataset, self.historic_dataset_version, self.historic_sets, self.historic_documents = \
            create_datatype_models("testing", self.set_names, self.seeds, 50)
        self.dataset_version = DatasetVersion.objects.create(dataset=self.dataset)
        for historic_set in self.historic_sets:
            self.dataset_version.historic_sets.add(historic_set)
        for seed in seed_generator("simple", 50, self.sequence_properties):
            HttpTikaResourceFactory.create(url=seed["url"])

    def test_invalid_set_outcome(self):
        harvest_entity = HarvestEntity.objects.get(source__module="merge")
        harvest_set = Set.objects.create(
            name="merge:merge_set",
            pending_at=None,  # HarvestSet does not become pending until all data from source has been pulled
            identifier="srn",
            dataset_version=self.dataset_version
        )
        HarvestState.objects.create(
            dataset=self.dataset,
            harvest_set=harvest_set,
            entity=harvest_entity,
            set_specification="merge_set"
        )
        seeding_patch_target = "core.tasks.harvest.source.HttpSeedingProcessor.__call__"
        seeding_patch_value = document_generator("merge", 44, 10, harvest_set, self.sequence_properties)
        with patch(seeding_patch_target, return_value=seeding_patch_value) as seeding_processor_call:
            harvest_source("testing", "merge", "merge_set", asynchronous=False)
        # Assert call to seeder
        seeding_processor_call.assert_called_with("merge_set", "1970-01-01T00:00:00Z")
        # Assert DatasetVersion
        dataset_version = DatasetVersion.objects.get(id=self.dataset_version.id)
        self.assertIsNone(dataset_version.pending_at)
        # Assert Set
        self.assertEqual(self.dataset_version.sets.count(), 1)
        for result_set in self.dataset_version.sets.all():
            self.assertIsNone(result_set.pending_at)
            self.assertEquals(
                harvest_set.id, result_set.id,
                "Expected the existing Set to copy Documents to keep propagating harvester tasks"
            )
            self.assertEqual(
                result_set.documents.exclude(pending_at=None).count(), 0,
                "Expected all historic Documents to not be pending"
            )
