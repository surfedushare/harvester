from django.test import TestCase
from django.utils.timezone import now

from testing.constants import SEED_DEFAULTS
from testing.models import Dataset, DatasetVersion, Set, TestDocument


class HttpSeedingProcessorTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.current_time = now()

    def setUp(self) -> None:
        super().setUp()
        self.dataset = Dataset.objects.create(name="test", is_harvested=True)
        self.dataset_version = DatasetVersion.objects.create(dataset=self.dataset)
        self.set = Set.objects.create(name="test", identifier="srn", dataset_version=self.dataset_version)
        self.ignored_document = TestDocument(
            collection=self.set,
            pipeline={"tika": {"success": True}},
            properties={
                "state": "active"
            },
            pending_at=None,
            finished_at=self.current_time
        )
        self.ignored_document.clean()
        self.ignored_document.save()
        # We reload the ignored_document here, because Django will cause very minor updates while reloading,
        # that we want to ignore for the tests
        self.ignored_document = TestDocument.objects.get(id=self.ignored_document.id)

    def assert_results(self, results, extra_keys=None, preexisting_document_ids=None):
        extra_keys = extra_keys or []
        extra_keys.append("srn")
        preexisting_document_ids = preexisting_document_ids or []
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
                self.assertEqual(sorted(result.properties.keys()), sorted(list(SEED_DEFAULTS.keys()) + extra_keys))
                if result.id not in preexisting_document_ids:
                    self.assertFalse(result.pipeline, "Expected TestDocument without further pipeline processing")
                    self.assertFalse(result.derivatives, "Expected TestDocument without processing results")
                    if result.state == TestDocument.States.ACTIVE:
                        self.assertTrue(result.pending_at, "Expected new TestDocuments to be pending for processing")
                        self.assertIsNone(result.finished_at, "Expected new TestDocuments to not be finished")
                    else:
                        self.assertIsNone(result.pending_at, "Expected non-active TestDocuments to be finished")
                        self.assertTrue(result.finished_at, "Expected non-active TestDocuments to be finished")
                self.assertEqual(result.collection.id, self.set.id, "Expected TestDocument to use Set as collection")
                self.assertEqual(
                    result.dataset_version.id,
                    self.dataset_version.id,
                    "Expected TestDocument to specify the DatasetVersion"
                )

    def assert_documents(self, expected_documents=20):
        self.assertEqual(
            self.set.documents.count(), expected_documents + 1,
            f"Expected {expected_documents} generated simple data structures and one pre-existing unchanged document"
        )
        # Pre-existing documents that are not in the harvest data should be left alone
        ignored_document = TestDocument.objects.get(id=self.ignored_document.id)
        self.assertEqual(ignored_document.metadata, self.ignored_document.metadata)
        self.assertEqual(ignored_document.identity, self.ignored_document.identity)
        self.assertEqual(ignored_document.pipeline, self.ignored_document.pipeline)
        self.assertEqual(ignored_document.properties, self.ignored_document.properties)
        self.assertEqual(ignored_document.derivatives, self.ignored_document.derivatives)
        self.assertIsNone(ignored_document.pending_at)
        self.assertIsNotNone(ignored_document.finished_at)
