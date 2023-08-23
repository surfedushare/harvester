from django.test import TestCase

from testing.constants import SEED_DEFAULTS
from testing.models import Set, TestDocument


class HttpSeedingProcessorTestCase(TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.set = Set.objects.create(name="test", identifier="srn")
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
                self.assertIsNotNone(result.id, "Expected a TestingDocument saved to the database")
                self.assertEqual(
                    result.collection_id, self.set.id,
                    "Expected a TestingDocument as part of test Set (aka Collection)"
                )
                self.assertIsNotNone(result.identity, "Expected Set to prescribe the identity for TestingDocument")
                self.assertTrue(sorted(result.properties.keys()), sorted(SEED_DEFAULTS.keys()))
                self.assertFalse(result.pipeline, "Expected TestingDocument without further pipeline processing")
                self.assertFalse(result.derivatives, "Expected TestingDocument without processing results")
                self.assertTrue(result.pending_at, "Expected new TestingDocuments to be pending for processing")

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
