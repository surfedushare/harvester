from unittest.mock import patch
from datetime import datetime

from django.test import TestCase
from django.utils.timezone import make_aware

from core.constants import DeletePolicies
from sources.tasks.entities import harvest_entities
from sources.models.harvest import HarvestEntity
from testing.constants import ENTITY_SEQUENCE_PROPERTIES
from testing.utils.factories import create_datatype_models
from testing.utils.generators import seed_generator
from testing.models import (Dataset, DatasetVersion, HarvestState, Set, TestDocument, MockHarvestResource,
                            MockIdsResource, MockDetailResource)


class HarvestEntitiesTestCase(TestCase):

    fixtures = ["test-sources-harvest-models"]

    dataset = None

    def setUp(self):
        super().setUp()
        self.simple_entity = HarvestEntity.objects.get(source__module="simple")
        self.merge_entity = HarvestEntity.objects.get(source__module="merge")
        MockHarvestResource.objects.create(uri="/mocks/entity/simple/1970-01-01T00:00:00Z")
        MockIdsResource.objects.create(uri="/mocks/entity/merge/1970-01-01T00:00:00Z/ids")
        MockDetailResource.objects.create(uri="/mocks/entity/merge/0")

    def assert_harvest_state(self, harvest_state):
        self.assertEqual(harvest_state.dataset.id, self.dataset.id)
        self.assertIn(harvest_state.entity, [self.simple_entity, self.merge_entity])
        self.assertIsInstance(harvest_state.harvest_set, Set)
        self.assertEqual(harvest_state.harvested_at, make_aware(datetime(year=1970, month=1, day=1)))
        self.assertIsInstance(harvest_state.purge_after, datetime)

    def assert_harvest_set(self, harvest_set, historic_docs):
        self.assertIsInstance(harvest_set.dataset_version, DatasetVersion)
        self.assertIn(harvest_set.name, ["simple:simple_set", "merge:merge_set"])
        entity_type, set_specification = harvest_set.name.split(":")
        entity = HarvestEntity.objects.get(source__module=entity_type)
        self.assertEqual(harvest_set.delete_policy, entity.delete_policy)
        self.assertEqual(harvest_set.documents.count(), historic_docs)

    def assert_dataset_version(self, dataset_version, historic_sets):
        self.assertEqual(dataset_version.dataset.id, self.dataset.id)
        self.assertEqual(dataset_version.sets.count(), 2)
        self.assertEqual(dataset_version.historic_sets.count(), historic_sets)

    def assert_harvest_entities(self, dataset_versions, harvest_source_mock):
        self.assertIsInstance(dataset_versions, list)
        self.assertEqual(len(dataset_versions), 1)
        self.assertEqual(
            dataset_versions[0][0], "testing.datasetversion",
            "Expected app_label and model_name as part of output about dataset versions"
        )
        self.assertGreater(
            dataset_versions[0][1], 0,
            "Expected an id integer as part of output about dataset versions"
        )
        # Assert call to harvest_source
        self.assertEqual(harvest_source_mock.call_count, 2)
        harvest_source_mock.assert_any_call("testing", "simple", "simple_set", asynchronous=False)
        harvest_source_mock.assert_any_call("testing", "merge", "merge_set", asynchronous=False)
        # Assert HarvestState
        self.assertEqual(
            HarvestState.objects.all().count(), 2,
            "Expected two harvest_state instances based on two sources in the fixtures"
        )
        for harvest_state in HarvestState.objects.all():
            self.assert_harvest_state(harvest_state)


class TestInitialHarvestEntities(HarvestEntitiesTestCase):

    def setUp(self):
        super().setUp()
        self.dataset = Dataset.objects.create(name="test", is_harvested=True)

    @patch("sources.tasks.entities.harvest_source")
    def test_harvest_entities(self, harvest_source_mock):
        dataset_versions = harvest_entities(HarvestEntity.EntityType.TEST, asynchronous=False)
        self.assert_harvest_entities(dataset_versions, harvest_source_mock)
        # Assert Set
        self.assertEqual(
            Set.objects.all().count(), 2,
            "Expected two harvest_set instances based on two sources in the fixtures"
        )
        for harvest_set in Set.objects.all():
            self.assertIsNone(
                harvest_set.pending_at,
                "Expected new Set not to be pending until harvest_source is done with collecting metadata"
            )
            self.assert_harvest_set(harvest_set, historic_docs=0)
        # Assert DatasetVersion
        self.assertEqual(
            DatasetVersion.objects.all().count(), 1,
            "Expected a single DatasetVersion to get created for an initial harvest"
        )
        for dataset_version in DatasetVersion.objects.all():
            self.assertIsNotNone(
                dataset_version.pending_at,
                "Expected new DatasetVersion to be pending if harvest_source doesn't run"
            )
            self.assert_dataset_version(dataset_version, historic_sets=0)
        # Assert resources
        self.assertEqual(
            MockHarvestResource.objects.all().count(), 0,
            "Expected resources to get deleted because of implicit reset (no historic data available)"
        )
        self.assertEqual(
            MockDetailResource.objects.all().count(), 0,
            "Expected resources to get deleted because of implicit reset (no historic data available)"
        )


class TestDeltaHarvestEntities(HarvestEntitiesTestCase):

    dataset_version = None
    harvest_set = None
    documents = []

    def setUp(self) -> None:
        super().setUp()
        self.set_names = ["simple:simple_set", "merge:merge_set"]
        self.seeds = list(seed_generator("simple", 10, ENTITY_SEQUENCE_PROPERTIES["simple"]))
        self.dataset, self.dataset_version, self.sets, self.documents = create_datatype_models(
            "testing", self.set_names,
            self.seeds, 5
        )
        self.merge_document = next((doc for doc in self.documents if doc.collection.name == "merge:merge_set"))
        self.invalid_document = self.documents[0]
        self.invalid_document.pipeline = {
            "check_url": {"success": False},
        }
        self.invalid_document.derivatives = {
            "check_url": {"status": 504}
        }
        self.invalid_document.save()
        self.failed_document = self.documents[1]
        self.failed_document.pipeline = {
            "check_url": {"success": True},
            "tika": {"success": False}
        }
        self.failed_document.derivatives = {
            "check_url": {"status": 200},
            "tika": {"texts": []}
        }
        self.failed_document.save()
        self.unprocessed_document = self.documents[2]
        self.inactive_document = self.documents[3]
        self.inactive_document.state = TestDocument.States.INACTIVE
        self.inactive_document.save()
        for doc in self.documents[4:]:
            doc.pipeline = {
                "check_url": {"success": True},
                "tika": {"success": True}
            }
            doc.derivatives = {
                "check_url": {"status": 200},
                "tika": {"texts": ["text from Tika"]}
            }
            doc.save()

    @patch("sources.tasks.entities.harvest_source")
    def test_harvest_entities(self, harvest_source_mock):
        dataset_versions = harvest_entities(HarvestEntity.EntityType.TEST, asynchronous=False)
        self.assert_harvest_entities(dataset_versions, harvest_source_mock)
        # Assert Set
        self.assertEqual(
            Set.objects.all().count(), 4,
            "Expected two new harvest_set instances based on two sources in the fixtures and two historic harvest_sets"
        )
        for harvest_set in Set.objects.exclude(dataset_version=self.dataset_version):  # excludes historic sets
            self.assertIsNone(
                harvest_set.pending_at,
                "Expected new Set not to be pending until harvest_source is done with collecting metadata"
            )
            self.assert_harvest_set(harvest_set, historic_docs=5)
        # Assert DatasetVersion
        self.assertEqual(
            DatasetVersion.objects.all().count(), 2,
            "Expected a single DatasetVersion to get created and one historic DatasetVersion to exist"
        )
        for dataset_version in DatasetVersion.objects.exclude(id=self.dataset_version.id):  # excludes historic data
            self.assertIsNotNone(
                dataset_version.pending_at,
                "Expected new DatasetVersion to be pending if harvest_source doesn't run"
            )
            self.assert_dataset_version(dataset_version, historic_sets=2)
        # Assert resources
        self.assertEqual(
            MockIdsResource.objects.all().count(), 0,
            "Expected resources for 'merge' entity to get deleted because of delete_policy=no"
        )
        self.assertEqual(
            MockDetailResource.objects.all().count(), 0,
            "Expected resources for 'merge' entity to get deleted because of delete_policy=no"
        )
        # Assert documents
        # Invalid document
        self.assertEqual(TestDocument.objects.all().count(), 20)
        invalid_document = TestDocument.objects \
            .exclude(dataset_version=self.dataset_version) \
            .filter(identity=self.invalid_document.identity) \
            .last()
        self.assertEqual(
            invalid_document.pipeline, {"check_url": {"success": False}},
            "Expected check_url to propagate between harvests"
        )
        self.assertEqual(
            invalid_document.derivatives, {"check_url": {"status": 504}},
            "Expected derivatives to get reset"
        )
        self.assertTrue(invalid_document.properties, "Expected properties to remain intact")
        self.assertIsNone(invalid_document.pending_at, "Expected invalid document to remain finished")
        # Failed document
        failed_document = TestDocument.objects \
            .exclude(dataset_version=self.dataset_version) \
            .filter(identity=self.failed_document.identity) \
            .last()
        self.assertEqual(failed_document.pipeline, {"check_url": {"success": True}}, "Expected pipeline to get reset")
        self.assertEqual(
            failed_document.derivatives, {"check_url": {"status": 200}},
            "Expected derivatives to get reset"
        )
        self.assertTrue(failed_document.properties, "Expected properties to remain intact")
        self.assertIsInstance(failed_document.pending_at, datetime, "Expected failed document to become pending")
        # Unprocessed document
        unprocessed_document = TestDocument.objects \
            .exclude(dataset_version=self.dataset_version) \
            .filter(identity=self.unprocessed_document.identity) \
            .last()
        self.assertEqual(unprocessed_document.pipeline, {}, "Expected pipeline to remain as is")
        self.assertEqual(unprocessed_document.derivatives, {}, "Expected derivatives to remain as is")
        self.assertTrue(unprocessed_document.properties, "Expected properties to remain intact")
        self.assertIsInstance(
            unprocessed_document.pending_at, datetime,
            "Expected previously unprocessed document to become pending"
        )
        # Inactive document
        inactive_document = TestDocument.objects \
            .exclude(dataset_version=self.dataset_version) \
            .filter(identity=self.inactive_document.identity) \
            .last()
        self.assertEqual(inactive_document.pipeline, {}, "Expected pipeline to remain as is")
        self.assertEqual(inactive_document.derivatives, {}, "Expected derivatives to remain as is")
        self.assertTrue(inactive_document.properties, "Expected properties to remain intact")
        self.assertIsNone(inactive_document.pending_at, "Expected inactive document to remain unprocessed")
        # Success documents
        error_identities = [
            self.invalid_document.identity, self.failed_document.identity, self.unprocessed_document.identity,
            self.inactive_document.identity
        ]
        success_document = TestDocument.objects \
            .exclude(dataset_version=self.dataset_version, identity__in=error_identities) \
            .first()
        self.assertEqual(
            success_document.pipeline,
            {
                "check_url": {"success": True},
                "tika": {"success": True}
            },
            "Expected pipeline to remain intact"
        )
        self.assertEqual(
            success_document.derivatives,
            {
                "check_url": {"status": 200},
                "tika": {"texts": ["text from Tika"]}
            },
            "Expected derivatives to remain intact"
        )
        self.assertTrue(success_document.properties, "Expected properties to remain intact")
        self.assertIsNone(success_document.pending_at, "Expected document not to become pending automatically")
        # Merge document
        merge_document = TestDocument.objects \
            .exclude(dataset_version=self.dataset_version) \
            .filter(identity=self.merge_document.identity) \
            .last()
        self.assertIsNotNone(
            merge_document.metadata["deleted_at"],
            "Expected document coming from delete_policy=no to always get 'soft' deleted before harvesting starts"
        )
        self.assertEqual(
            merge_document.properties["state"], merge_document.States.ACTIVE,
            "Expected document coming from delete_policy=no to always get 'soft' deleted without setting properties"
        )
        self.assertEqual(
            merge_document.state, merge_document.States.ACTIVE,
            "Expected document coming from delete_policy=no to always get 'soft' deleted without setting state"
        )

    @patch("sources.tasks.entities.harvest_source")
    def test_keep_resources(self, harvest_source_mock):
        """
        Testing whether resources can be re-used during harvest process.

        We'll swap delete policies for Simple and Merge entities.
        Then we should keep MockDetailResource, because Merge now indicates it wants to re-use them,
        with its new transient delete policy.
        """
        self.simple_entity.delete_policy = DeletePolicies.NO
        self.simple_entity.save()
        self.merge_entity.delete_policy = DeletePolicies.TRANSIENT
        self.merge_entity.save()
        # Making the test call
        harvest_entities(HarvestEntity.EntityType.TEST, asynchronous=False)
        # Assert call to harvest_source
        self.assertEqual(harvest_source_mock.call_count, 2)
        harvest_source_mock.assert_any_call("testing", "simple", "simple_set", asynchronous=False)
        harvest_source_mock.assert_any_call("testing", "merge", "merge_set", asynchronous=False)
        # Assert resources
        self.assertEqual(
            MockHarvestResource.objects.all().count(), 0,
            "Expected resources for 'simple' entity to get deleted because of delete_policy=no"
        )
        self.assertEqual(
            MockDetailResource.objects.all().count(), 1,
            "Expected resources for 'merge' entity to remain where possible because of delete_policy=transient"
        )
