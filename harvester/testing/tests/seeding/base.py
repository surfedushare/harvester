from django.test import TestCase

from testing.constants import SEED_DEFAULTS
from testing.models import Dataset, DatasetVersion, Set, TestDocument


class HttpSeedingProcessorTestCase(TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.dataset = Dataset.objects.create(name="test", is_harvested=True)
        self.dataset_version = DatasetVersion.objects.create(dataset=self.dataset)
        self.set = Set.objects.create(name="test", identifier="srn", dataset_version=self.dataset_version)
        self.ignored_document = TestDocument.objects.create(
            collection=self.set,
            pipeline={},
            properties={},
            pending_at=None
        )

    def assert_results(self, results):
        # Assert results
        for batch in results:
            self.assertIsInstance(batch, list)
            for result in batch:
                self.assertIsInstance(result, TestDocument)
                self.assertIsNotNone(result.id, "Expected a TestDocument saved to the database")
                self.assertEqual(
                    result.collection_id, self.set.id,
                    "Expected a TestingDocument as part of test Set (aka Collection)"
                )
                self.assertIsNotNone(result.identity, "Expected Set to prescribe the identity for TestDocument")
                self.assertTrue(sorted(result.properties.keys()), sorted(SEED_DEFAULTS.keys()))
                self.assertFalse(result.pipeline, "Expected TestDocument without further pipeline processing")
                self.assertFalse(result.derivatives, "Expected TestDocument without processing results")
                self.assertTrue(result.pending_at, "Expected new TestDocuments to be pending for processing")
                self.assertEqual(result.collection.id, self.set.id, "Expected TestDocument to use Set as collection")
                self.assertEqual(
                    result.dataset_version.id,
                    self.dataset_version.id,
                    "Expected TestDocument to specify the DatasetVersion"
                )

    def assert_documents(self):
        self.assertEqual(
            self.set.documents.count(), 20 + 1,
            "Expected 20 generated simple data structures and one pre-existing unchanged document"
        )
        # Pre-existing documents that are not in the harvest data should be left alone
        ignored_document = TestDocument.objects.get(id=self.ignored_document.id)
        self.assertFalse(ignored_document.identity)
        self.assertFalse(ignored_document.pipeline)
        self.assertFalse(ignored_document.properties)
        self.assertFalse(ignored_document.derivatives)
        self.assertIsNone(ignored_document.pending_at)