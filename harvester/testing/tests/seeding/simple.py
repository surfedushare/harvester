from datetime import datetime
from unittest.mock import patch

from django.utils.timezone import make_aware

from core.processors import HttpSeedingProcessor
from testing.tests.seeding.base import HttpSeedingProcessorTestCase
from testing.models import MockHarvestResource, TestDocument
from testing.sources.simple import SEEDING_PHASES


class TestSimpleHttpSeedingProcessor(HttpSeedingProcessorTestCase):

    def test_seeding(self):
        processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })
        results = processor("simple", "1970-01-01T00:00:00Z")

        self.assert_results(results)
        self.assert_documents()

        # Assert resources
        self.assertEqual(MockHarvestResource.objects.all().count(), 2, "Expected two requests to mock data endpoints")
        for resource in MockHarvestResource.objects.all():
            self.assertTrue(resource.success)
            self.assertEqual(resource.request["args"], ["simple", "1970-01-01T00:00:00Z"])


UPDATE_PARAMETERS = {
    "size": 20,
    "page_size": 10,
    "deletes": 3  # deletes the 1st seed and every 3rd seed after that
}


class TestSimpleUpdateHttpSeedingProcessor(HttpSeedingProcessorTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.deleted_document = TestDocument(
            dataset_version=self.dataset_version,
            collection=self.set,
            pipeline={},
            properties={
                "state": "active",
                "set": "surf:testing",
                "external_id": 0,
                "srn": "surf:testing:0",
                "url": "http://testserver/file/0",
                "title": "title for 0",
                "access_rights": "OpenAccess",
                "copyright": None,
            },
            pending_at=None,
            finished_at=self.current_time
        )
        self.deleted_document.clean()
        self.deleted_document.save()
        self.updated_document = TestDocument(
            dataset_version=self.dataset_version,
            collection=self.set,
            pipeline={
                "tika": {
                    "success": True
                }
            },
            properties={
                "state": "active",
                "set": "surf:testing",
                "external_id": 1,
                "srn": "surf:testing:1",
                "url": "http://testserver/file/1",
                "title": "title for 1 before update",  # this is the important part that will change during the update
                "access_rights": "OpenAccess",
                "copyright": None,
            },
            pending_at=None,
            finished_at=self.current_time
        )
        self.updated_document.clean()
        self.updated_document.save()
        self.unchanged_document = TestDocument(
            dataset_version=self.dataset_version,
            collection=self.set,
            identity="surf:testing:2",
            pipeline={
                "tika": {
                    "success": True
                }
            },
            properties={
                "state": "active",
                "set": "surf:testing",
                "external_id": 2,
                "srn": "surf:testing:2",
                "url": "http://testserver/file/2",
                "title": "title for 2",
                "access_rights": "OpenAccess",
                "copyright": None,
            },
            pending_at=None,
            finished_at=self.current_time
        )
        self.unchanged_document.clean()
        self.unchanged_document.save()

    @patch.object(MockHarvestResource, "PARAMETERS", UPDATE_PARAMETERS)
    def test_seeding(self):
        processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })
        results = processor("simple", "1970-01-01T00:00:00Z")

        self.assert_results(
            results,
            preexisting_document_ids=[
                self.ignored_document.id,
                self.deleted_document.id,
                self.updated_document.id,
                self.unchanged_document.id
            ]
        )
        self.assert_documents()

        # Assert delete document
        deleted_document = TestDocument.objects.get(id=self.deleted_document.id)
        deleted_at = deleted_document.metadata["deleted_at"]
        self.assertIsNotNone(deleted_at)
        self.assertNotEqual(deleted_at, deleted_document.metadata["created_at"])
        self.assertEqual(deleted_at, deleted_document.metadata["modified_at"])

        # Assert update document
        updated_document = TestDocument.objects.get(id=self.updated_document.id)
        updated_at = updated_document.metadata["modified_at"]
        self.assertIsNotNone(updated_at)
        self.assertNotEqual(updated_at, updated_document.metadata["created_at"])
        self.assertIsNone(updated_document.metadata["deleted_at"])
        self.assertEqual(updated_document.properties["title"], "title for 1", "Expected the title to get updated")
        self.assertFalse(
            updated_document.pending_at,
            "Expected pre-existing document without relevant update to not become pending for tasks"
        )
        self.assertIn(
            "tika", updated_document.pipeline,
            "Expected pre-existing document without relevant update to keep any pipeline state"
        )
        self.assertIsNone(updated_document.pending_at, "Did not expect title change to set Document as pending")
        self.assertEqual(
            updated_document.finished_at, self.current_time,
            "Expected title change not to change finished_at value"
        )

        # Assert unchanged document
        unchanged_document = TestDocument.objects.get(id=self.unchanged_document.id)
        self.assertEqual(unchanged_document.metadata["created_at"], unchanged_document.metadata["modified_at"])
        self.assertIsNone(unchanged_document.metadata["deleted_at"])
        self.assertEqual(unchanged_document.properties["title"], "title for 2", "Expected the title to remain as-is")
        self.assertIsNone(
            unchanged_document.pending_at,
            "Expected pre-existing document without update to not become pending for tasks"
        )
        self.assertEqual(
            unchanged_document.finished_at, self.current_time,
            "Expected unchanged document to keep finished_at same as at start of test"
        )
        self.assertIn(
            "tika", unchanged_document.pipeline,
            "Expected pre-existing document without update to keep any pipeline state"
        )
