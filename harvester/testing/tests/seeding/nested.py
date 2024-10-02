from unittest.mock import patch

from core.processors import HttpSeedingProcessor
from testing.tests.seeding.base import HttpSeedingProcessorTestCase
from testing.models import TestDocument, MockHarvestResource
from testing.sources.nested import SEEDING_PHASES


NESTING_PARAMETERS = {
    "size": 20,
    "page_size": 10,
    "nested": "simple"
}


class TestNestedHttpSeedingProcessor(HttpSeedingProcessorTestCase):

    @patch.object(MockHarvestResource, "PARAMETERS", NESTING_PARAMETERS)
    def test_seeding(self):
        processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })
        results = processor("nested", "1970-01-01T00:00:00Z")

        self.assert_results(results, extra_keys=["parent_id"])  # extraction method adds this key to defaults
        self.assert_documents(expected_documents=19)  # due to the way generated nested seeds get divided we loose one

        # Assert resources
        self.assertEqual(MockHarvestResource.objects.all().count(), 2, "Expected two requests to mock data endpoints")
        for resource in MockHarvestResource.objects.all():
            self.assertTrue(resource.success)
            self.assertEqual(resource.request["args"], ["nested", "1970-01-01T00:00:00Z"])


NESTED_DELETE_PARAMETERS = {
    "size": 20,
    "page_size": 10,
    "nested": "simple",
    "deletes": 4  # deletes the 1st seed and every 4th seed after that
}


class TestNestedDeletesHttpSeedingProcessor(HttpSeedingProcessorTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.updated_document = TestDocument(
            dataset_version=self.dataset_version,
            collection=self.set,
            pipeline={"tika": {"success": True}},
            properties={
                "state": "active",
                "set": "surf:testing",
                "external_id": 1,
                "srn": "surf:testing:1",
                "parent_id": "surf:testing:2",
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
                "parent_id": "surf:testing:2",
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
        self.deleted_document = TestDocument(
            dataset_version=self.dataset_version,
            collection=self.set,
            pipeline={"tika": {"success": True}},
            properties={
                "state": "active",
                "set": "surf:testing",
                "external_id": 3,
                "srn": "surf:testing:3",
                "parent_id": "surf:testing:4",
                "url": "http://testserver/file/3",
                "title": "title for 3",
                "access_rights": "OpenAccess",
                "copyright": None,
            },
            pending_at=None,
            finished_at=self.current_time
        )
        self.deleted_document.clean()
        self.deleted_document.save()

    @patch.object(MockHarvestResource, "PARAMETERS", NESTED_DELETE_PARAMETERS)
    def test_seeding(self):
        processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })
        results = processor("nested", "1970-01-01T00:00:00Z")

        self.assert_results(
            results,
            preexisting_document_ids=[
                self.ignored_document.id,
                self.updated_document.id,
                self.unchanged_document.id,
                self.deleted_document.id],
            extra_keys=["parent_id"]
        )
        self.assert_documents(expected_documents=16)

        # Assert delete document
        deleted_document = TestDocument.objects.get(id=self.deleted_document.id)
        deleted_at = deleted_document.metadata["deleted_at"]
        self.assertIsNotNone(deleted_at)
        self.assertNotEqual(deleted_at, deleted_document.metadata["created_at"])
        self.assertEqual(deleted_at, deleted_document.metadata["modified_at"])
        self.assertEqual(deleted_document.properties["parent_id"], "surf:testing:4")

        # Assert update document
        updated_document = TestDocument.objects.get(id=self.updated_document.id)
        updated_at = updated_document.metadata["modified_at"]
        self.assertIsNotNone(updated_at)
        self.assertNotEqual(updated_at, updated_document.metadata["created_at"])
        self.assertIsNone(updated_document.metadata["deleted_at"])
        self.assertEqual(updated_document.properties["title"], "title for 1")
        self.assertEqual(updated_document.properties["parent_id"], "surf:testing:2")
        self.assertIsNone(updated_document.pending_at, "Did not expect title change to set Document as pending")
        self.assertEqual(
            updated_document.finished_at, self.current_time,
            "Expected title change not to change finished_at value"
        )

        # Assert unchanged document
        unchanged_document = TestDocument.objects.get(id=self.unchanged_document.id)
        self.assertEqual(
            unchanged_document.metadata["created_at"].replace(microsecond=0),
            unchanged_document.metadata["modified_at"].replace(microsecond=0)
        )
        self.assertIsNone(unchanged_document.metadata["deleted_at"])
        self.assertEqual(unchanged_document.properties["title"], "title for 2")
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
        self.assertEqual(unchanged_document.properties["parent_id"], "surf:testing:2")
