from unittest.mock import patch
from datetime import datetime

from django.test import TestCase
from django.utils.timezone import make_aware, now

from sources.tasks.entities import harvest_entities
from sources.models.harvest import HarvestEntity
from testing.models import Dataset, DatasetVersion, HarvestState, Set, MockHarvestResource, MockDetailResource


class TestInitialHarvestEntities(TestCase):

    fixtures = ["test-sources-harvest-models"]

    def setUp(self):
        super().setUp()
        self.simple_entity = HarvestEntity.objects.get(source__module="simple")
        self.merge_entity = HarvestEntity.objects.get(source__module="merge")
        self.dataset = Dataset.objects.create(name="test", is_harvested=True)
        MockHarvestResource.objects.create(
            uri="localhost:8888/mocks/entity/simple_set",
            since=now(),
            set_specification="simple_set"
        )
        MockDetailResource.objects.create(uri="localhost:8888/mocks/entity/merge_set/0")

    def assert_harvest_state(self, harvest_state):
        self.assertEqual(harvest_state.dataset.id, self.dataset.id)
        self.assertIn(harvest_state.entity, [self.simple_entity, self.merge_entity])
        self.assertIsInstance(harvest_state.harvest_set, Set)
        self.assertEqual(harvest_state.harvested_at, make_aware(datetime(year=1970, month=1, day=1)))
        self.assertIsInstance(harvest_state.purge_after, datetime)

    def assert_harvest_set(self, harvest_set):
        self.assertIsInstance(harvest_set.dataset_version, DatasetVersion)
        self.assertIn(harvest_set.name, ["simple:simple_set", "merge:merge_set"])
        entity_type, set_specification = harvest_set.name.split(":")
        entity = HarvestEntity.objects.get(source__module=entity_type, set_specification=set_specification)
        self.assertEqual(harvest_set.delete_policy, entity.delete_policy)

    def assert_dataset_version(self, dataset_version):
        self.assertEqual(dataset_version.dataset.id, self.dataset.id)
        self.assertEqual(dataset_version.sets.count(), 2)
        self.assertEqual(dataset_version.historic_sets.count(), 0)

    @patch("sources.tasks.entities.harvest_source")
    def test_harvest_entities(self, harvest_source_mock):
        harvest_entities(HarvestEntity.EntityType.TEST, asynchronous=False)
        # Assert call to harvest_source
        self.assertEqual(harvest_source_mock.call_count, 2)
        harvest_source_mock.assert_any_call("testing", "simple", asynchronous=False)
        harvest_source_mock.assert_any_call("testing", "merge", asynchronous=False)
        # Assert HarvestState
        self.assertEqual(
            HarvestState.objects.all().count(), 2,
            "Expected two harvest_state instances based on two sources in the fixtures"
        )
        for harvest_state in HarvestState.objects.all():
            self.assert_harvest_state(harvest_state)
        # Assert Set
        self.assertEqual(
            Set.objects.all().count(), 2,
            "Expected two harvest_set instances based on two sources in the fixtures"
        )
        for harvest_set in Set.objects.all():
            self.assert_harvest_set(harvest_set)
        # Assert DatasetVersion
        self.assertEqual(
            DatasetVersion.objects.all().count(), 1,
            "Expected a single DatasetVersion to get created for an initial harvest"
        )
        for dataset_version in DatasetVersion.objects.all():
            self.assert_dataset_version(dataset_version)
        # Assert resources
        self.assertEqual(MockHarvestResource.objects.all().count(), 0)
        self.assertEqual(MockDetailResource.objects.all().count(), 0)
