from datetime import datetime
from unittest.mock import patch

from django.utils.timezone import make_aware

from core.processors import HttpSeedingProcessor
from testing.constants import ENTITY_SEQUENCE_PROPERTIES
from testing.tests.seeding.base import HttpSeedingProcessorTestCase
from testing.utils.generators import document_generator
from testing.models import TestDocument, MockIdsResource, MockDetailResource
from testing.sources.merge import SEEDING_PHASES


class TestMergeHttpSeedingProcessor(HttpSeedingProcessorTestCase):

    def test_seeding(self):
        processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })
        results = processor("merge", "1970-01-01T00:00:00Z")

        self.assert_results(results)
        self.assert_documents()

        # Assert list resource
        self.assertEqual(
            MockIdsResource.objects.all().count(), 1,
            "Expected one requests to list mock data endpoints"
        )
        list_resource = MockIdsResource.objects.first()
        self.assertTrue(list_resource.success)
        self.assertEqual(list_resource.request["args"], ["merge", "1970-01-01T00:00:00Z"])
        # Assert detail resources
        self.assertEqual(
            MockDetailResource.objects.all().count(), 20,
            "Expected one request to detail mock data endpoints for each element in list data response"
        )
        for ix, resource in enumerate(MockDetailResource.objects.all()):
            self.assertTrue(resource.success)
            self.assertEqual(resource.request["args"], ["merge", ix])


UPDATE_PARAMETERS = {
    "size": 20,
    "page_size": 10,
    "deletes": 3  # deletes the 1st seed and every 3rd seed after that
}


class TestMergeUpdateHttpSeedingProcessor(HttpSeedingProcessorTestCase):
    """
    The setup of this test will use a generator that creates deleted documents.
    When running the seeder this should un-delete almost all seeds and
    shouldn't update the metadata from generated documents, unless real updates came through the seeder.
    """

    def setUp(self) -> None:
        super().setUp()
        self.documents = list(
            document_generator("merge", 20, 10, self.set, ENTITY_SEQUENCE_PROPERTIES["merge"], {"days": 1},
                               state=TestDocument.States.DELETED)
        )
        TestDocument.objects.all().update(finished_at=self.current_time, pending_at=None)
        self.updated_document = TestDocument.objects.get(properties__srn="surf:testing:1")
        self.updated_document.properties["title"] = "title for 1 before update"
        self.updated_document.save()
        self.unchanged_document = TestDocument.objects.get(properties__srn="surf:testing:2")
        self.unchanged_document.metadata["hash"] = "68ec32dbc79b1a5fc40caaec4134b4ba8b12bd8f"
        self.unchanged_document.pipeline["tika"] = {"success": True}
        self.unchanged_document.save()

    @patch.object(MockIdsResource, "PARAMETERS", UPDATE_PARAMETERS)
    def test_seeding(self):
        processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })
        results = processor("merge", "1970-01-01T00:00:00Z")

        self.assert_results(
            results,
            preexisting_document_ids=[
                self.ignored_document.id,
                *[doc.id for batch in self.documents for doc in batch]
            ]
        )
        self.assert_documents()

        # Assert delete document
        deleted_document = TestDocument.objects.get(identity="surf:testing:0")
        deleted_at = deleted_document.metadata["deleted_at"]
        self.assertIsNotNone(deleted_at)
        self.assertEqual(
            deleted_at, deleted_document.metadata["created_at"],
            "Due to testing setup we create the documents in deleted state"
        )
        self.assertEqual(deleted_at, deleted_document.metadata["modified_at"])

        # Assert update document
        updated_document = TestDocument.objects.get(identity="surf:testing:1")
        updated_at = updated_document.metadata["modified_at"]
        self.assertIsNotNone(updated_at)
        self.assertNotEqual(updated_at, updated_document.metadata["created_at"])
        self.assertIsNone(updated_document.metadata["deleted_at"])
        self.assertEqual(updated_document.properties["title"], "title for 1", "Expected the title to get updated")
        self.assertIsNone(updated_document.pending_at, "Did not expect title change to set Document as pending")
        self.assertEqual(
            updated_document.finished_at, self.current_time,
            "Expected title change not to change finished_at value"
        )

        # Assert unchanged document
        unchanged_document = TestDocument.objects.get(identity="surf:testing:2")
        self.assertEqual(unchanged_document.metadata["created_at"], unchanged_document.metadata["modified_at"],
                         "Unexpected update for unchanged document, is the hash set in the setUp method still correct?")
        self.assertIsNone(unchanged_document.metadata["deleted_at"])
        self.assertEqual(unchanged_document.properties["title"], "title for 2", "Expected the title to remain as-is")
        self.assertIsNone(
            unchanged_document.pending_at,
            "Expected pre-existing document without update to not become pending"
        )
        self.assertEqual(
            unchanged_document.finished_at, self.current_time,
            "Expected unchanged document to keep finished_at same as at start of test"
        )
        self.assertIn(
            "tika", unchanged_document.pipeline,
            "Expected pre-existing document without update to keep any pipeline state"
        )
