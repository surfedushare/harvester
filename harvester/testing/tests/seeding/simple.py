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
            self.assertEqual(resource.since, make_aware(datetime(year=1970, month=1, day=1)))


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
                "srn": "surf:testing:0",
                "external_id": 0,
                "url": "http://localhost:8888/file/0",
                "title": "title for 0"
            },
            pending_at=None
        )
        self.deleted_document.clean()
        self.deleted_document.save()
        self.updated_document = TestDocument.objects.create(
            dataset_version=self.dataset_version,
            collection=self.set,
            pipeline={},
            properties={
                "state": "active",
                "srn": "surf:testing:1",
                "external_id": 1,
                "url": "http://localhost:8888/file/1",
                "title": "title for 1 before update"  # this is the important part that will change during the update
            },
            pending_at=None
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
                "srn": "surf:testing:2",
                "external_id": 2,
                "url": "http://localhost:8888/file/2",
                "title": "title for 2"
            },
            pending_at=None
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
        self.assertEqual(updated_document.properties["title"], "title for 1")

        # Assert unchanged document
        unchanged_document = TestDocument.objects.get(id=self.unchanged_document.id)
        self.assertEqual(unchanged_document.metadata["created_at"], unchanged_document.metadata["modified_at"])
        self.assertIsNone(unchanged_document.metadata["deleted_at"])
        self.assertEqual(unchanged_document.properties["title"], "title for 2")
        self.assertFalse(
            unchanged_document.pending_at,
            "Expected pre-existing document without update to not become pending"
        )
        self.assertIn(
            "tika", unchanged_document.pipeline,
            "Expected pre-existing document without update to keep any pipeline state"
        )
