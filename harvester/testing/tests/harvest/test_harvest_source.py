from unittest.mock import patch
from copy import copy
from datetime import datetime

from django.test import TestCase
from django.utils.timezone import now
from django.utils.timezone import make_aware

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

    def test_initial(self):
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
                "texts": [f"Tika content for http://testserver/file/{ix}"]
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

    def test_initial_manual(self):
        # Setup data for this test
        harvest_entity = HarvestEntity.objects.get(source__module="simple")
        harvest_entity.is_manual = True
        harvest_entity.save()
        beginning_of_time = make_aware(datetime(year=1970, month=1, day=1))
        # Call the harvest_source task with patched HttpSeedingProcessor output
        seeding_patch_target = "core.tasks.harvest.source.HttpSeedingProcessor.__call__"
        seeding_patch_value = document_generator("simple", 11, 10, self.set, self.sequence_properties)
        with patch(seeding_patch_target, return_value=seeding_patch_value) as seeding_processor_call:
            harvest_source("testing", "simple", "simple_set", asynchronous=False)
        # Assert that seeding_processor was never called
        self.assertEqual(seeding_processor_call.call_count, 0)
        # Harvest state asserts
        harvest_state = HarvestState.objects.get(id=self.state.id)
        self.assertEqual(
            harvest_state.harvested_at, beginning_of_time,
            "Expected datetime value for HarvestState.harvested_at to remain the same"
        )
        # Assert Set
        harvest_set = harvest_state.harvest_set
        self.assertEqual(harvest_set.documents.all().count(), 0)
        self.assertIsNone(harvest_set.pending_at)
        self.assertIsNotNone(harvest_set.finished_at, "Expected manual entities to still run Set tasks")
        # Assert DatasetVersion
        dataset_version = harvest_set.dataset_version
        self.assertIsNone(dataset_version.pending_at)
        self.assertIsNotNone(dataset_version.finished_at, "Expected manual entities to still run DatasetVersion tasks")
        self.assertEqual(dataset_version.sets.all().count(), 1)


class TestDeltaHarvestSource(TestCase):

    fixtures = ["test-sources-harvest-models"]

    def setUp(self) -> None:
        super().setUp()
        # Some testing variables
        self.current_time = now()
        self.sequence_properties = ENTITY_SEQUENCE_PROPERTIES["simple"]
        self.set_names = ["simple:simple_set", "merge:merge_set"]
        # Historic data
        self.seeds = list(seed_generator("simple", 100, self.sequence_properties))
        self.dataset, self.historic_dataset_version, self.historic_sets, self.historic_documents = \
            create_datatype_models("testing", self.set_names, self.seeds, 50)
        # New dataset versions and sets
        self.dataset_version = DatasetVersion.objects.create(dataset=self.dataset)
        self.simple_set = Set.objects.create(
            name="simple:simple_set",
            pending_at=None,  # HarvestSet does not become pending until all data from source has been pulled
            identifier="srn",
            dataset_version=self.dataset_version
        )
        self.merge_set = Set.objects.create(
            name="merge:merge_set",
            pending_at=None,  # HarvestSet does not become pending until all data from source has been pulled
            identifier="srn",
            dataset_version=self.dataset_version,
            finished_at=self.current_time
        )
        for historic_set in self.historic_sets:
            self.dataset_version.historic_sets.add(historic_set)
            if historic_set.name == "simple:simple_set":  # simple_set has delete_policy=transient
                self.simple_set.copy_documents(historic_set)
        for seed in seed_generator("simple", 100, self.sequence_properties):
            HttpTikaResourceFactory.create(url=seed["url"])

    def assert_harvest_state(self, harvest_state_id, should_update_harvested_at=True, document_count=0,
                             pending_document_count=0):
        harvest_state = HarvestState.objects.get(id=harvest_state_id)
        # Harvest state asserts
        self.assertEqual(
            harvest_state.harvested_at > self.current_time, should_update_harvested_at,
            "Unexpected datetime value for HarvestState.harvested_at"
        )
        # Assert Set
        harvest_set = harvest_state.harvest_set
        self.assertEqual(harvest_set.documents.all().count(), document_count)
        self.assertEqual(harvest_set.documents.filter(pending_at__isnull=False).count(), pending_document_count)
        finished_document_count = document_count - pending_document_count
        self.assertEqual(harvest_set.documents.filter(finished_at__isnull=False).count(), finished_document_count)
        # Assert DatasetVersion
        dataset_version = harvest_set.dataset_version
        self.assertIsNone(dataset_version.pending_at)
        self.assertIsNotNone(dataset_version.finished_at)
        self.assertEqual(dataset_version.sets.all().count(), 2, "Expected a 'simple' and 'merge' set")
        self.assertEqual(
            dataset_version.sets.filter(finished_at__isnull=True).count(), 0,
            "Expected all Sets to be finished at end of the test"
        )

    def test_delta(self):
        # Setup data for this test
        harvest_entity = HarvestEntity.objects.get(source__module="simple")
        harvest_state = HarvestState.objects.create(
            dataset=self.dataset,
            harvest_set=self.simple_set,
            entity=harvest_entity,
            set_specification="simple_set",
            harvested_at=make_aware(datetime(year=2000, month=1, day=1))
        )
        pending_doc = self.simple_set.documents.last()
        pending_doc.pending_at = self.current_time
        pending_doc.finished_at = None
        pending_doc.save()
        # Call the harvest_source task with patched HttpSeedingProcessor output
        seeding_patch_target = "core.tasks.harvest.source.HttpSeedingProcessor.__call__"
        seeding_patch_value = document_generator("simple", 11, 10, self.simple_set, self.sequence_properties)
        with patch(seeding_patch_target, return_value=seeding_patch_value) as seeding_processor_call:
            harvest_source("testing", "simple", "simple_set", asynchronous=False)
        # Assert call to seeder which should receive the value of HarvestState.harvested_at datetime
        seeding_processor_call.assert_called_with("simple_set", "2000-01-01T00:00:00Z")
        # Assert data
        # The generator adds 11 documents regardless whether they are possibly updates.
        # Updating data is tested inside HttpSeedingProcessor and we patch that here.
        # The pending Document created at the start of this test should disappear,
        # as historic Documents get re-dispatched.
        self.assert_harvest_state(harvest_state_id=harvest_state.id, document_count=61)

    def test_delta_no_seeds(self):
        # Setup data for this test
        harvest_entity = HarvestEntity.objects.get(source__module="simple")
        harvest_state = HarvestState.objects.create(
            dataset=self.dataset,
            harvest_set=self.simple_set,
            entity=harvest_entity,
            set_specification="simple_set",
            harvested_at=make_aware(datetime(year=2000, month=1, day=1))
        )
        # Call the harvest_source task with patched HttpSeedingProcessor output
        seeding_patch_target = "core.tasks.harvest.source.HttpSeedingProcessor.__call__"
        with patch(seeding_patch_target, return_value=[]) as seeding_processor_call:
            harvest_source("testing", "simple", "simple_set", asynchronous=False)
        # Assert call to seeder which should receive the value of HarvestState.harvested_at datetime
        seeding_processor_call.assert_called_with("simple_set", "2000-01-01T00:00:00Z")
        # Assert data
        # We should end up with 50 Documents that already exist at the start of the test
        self.assert_harvest_state(harvest_state_id=harvest_state.id, document_count=50)

    def test_delta_pending_set(self):
        # Setup data for this test
        harvest_entity = HarvestEntity.objects.get(source__module="simple")
        self.simple_set.pending_at = self.current_time
        self.simple_set.save()
        harvest_state = HarvestState.objects.create(
            dataset=self.dataset,
            harvest_set=self.simple_set,
            entity=harvest_entity,
            set_specification="simple_set",
            harvested_at=make_aware(datetime(year=2000, month=1, day=1)),
        )
        # Call the harvest_source task with patched HttpSeedingProcessor output
        seeding_patch_target = "core.tasks.harvest.source.HttpSeedingProcessor.__call__"
        seeding_patch_value = document_generator("simple", 11, 10, self.simple_set, self.sequence_properties)
        with patch(seeding_patch_target, return_value=seeding_patch_value) as seeding_processor_call:
            harvest_source("testing", "simple", "simple_set", asynchronous=False)
        # Assert that seeding_processor was never called
        self.assertEqual(seeding_processor_call.call_count, 0)
        # Assert data
        # Sets and DatasetVersion should remain pending and HarvestState.harvested_at should not update
        harvest_state = HarvestState.objects.get(id=harvest_state.id)
        self.assertEqual(harvest_state.harvested_at, make_aware(datetime(year=2000, month=1, day=1)))
        self.assertIsNotNone(harvest_state.harvest_set.pending_at)
        self.assertIsNotNone(harvest_state.harvest_set.dataset_version.pending_at)

    def test_delta_manual(self):
        # Setup data for this test
        harvest_entity = HarvestEntity.objects.get(source__module="simple")
        harvest_entity.is_manual = True
        harvest_entity.save()
        harvest_state = HarvestState.objects.create(
            dataset=self.dataset,
            harvest_set=self.simple_set,
            entity=harvest_entity,
            set_specification="simple_set",
            harvested_at=make_aware(datetime(year=2000, month=1, day=1)),
        )
        # Call the harvest_source task with patched HttpSeedingProcessor output
        seeding_patch_target = "core.tasks.harvest.source.HttpSeedingProcessor.__call__"
        seeding_patch_value = document_generator("simple", 11, 10, self.simple_set, self.sequence_properties)
        with patch(seeding_patch_target, return_value=seeding_patch_value) as seeding_processor_call:
            harvest_source("testing", "simple", "simple_set", asynchronous=False)
        # Assert that seeding_processor was never called
        self.assertEqual(seeding_processor_call.call_count, 0)
        # Assert data
        # HarvestState.harvested_at should not get updated
        self.assert_harvest_state(harvest_state.id, should_update_harvested_at=False, document_count=50)

    def test_delta_failing_set_integrity_check(self):
        # Setup data for this test
        harvest_entity = HarvestEntity.objects.get(source__module="merge")
        harvest_state = HarvestState.objects.create(
            dataset=self.dataset,
            harvest_set=self.merge_set,
            entity=harvest_entity,
            set_specification="merge_set"
        )
        self.simple_set.finished_at = self.current_time
        self.simple_set.save()
        # Call the harvest_source task with patched HttpSeedingProcessor output
        seeding_patch_target = "core.tasks.harvest.source.HttpSeedingProcessor.__call__"
        seeding_patch_value = document_generator("merge", 44, 10, self.merge_set, self.sequence_properties)
        with patch(seeding_patch_target, return_value=seeding_patch_value) as seeding_processor_call:
            harvest_source("testing", "merge", "merge_set", asynchronous=False)
        # Assert call to seeder which should receive the value of HarvestState.harvested_at datetime
        seeding_processor_call.assert_called_with("merge_set", "1970-01-01T00:00:00Z")
        # Assert data
        # We expect to find the 50 old merge documents instead of 44 new merge documents
        # There's only one expected Set, because
        self.assert_harvest_state(harvest_state.id, document_count=50)
