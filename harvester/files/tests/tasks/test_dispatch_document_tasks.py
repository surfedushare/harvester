from unittest.mock import patch

from django.test import TestCase
from django.utils.timezone import now

from core.tasks import dispatch_document_tasks
from files.tests.factories import create_file_document_set
from files.models import FileDocument
from files.models.datatypes.file import default_document_tasks


class TestHarvestObjectFileDocument(TestCase):

    dataset_version = None
    set = None
    documents = []
    document = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dataset_version, cls.set, cls.documents = create_file_document_set(
            "test",
            [{"url": "https://example.com/1"}, {"url": "https://example.com/2"}, {"url": "https://youtu.be/3"}],
        )
        cls.document_1, cls.document_2, cls.youtube = cls.documents

    def test_get_primary_pending_tasks(self):
        pending_tasks_1 = self.document_1.get_pending_tasks()
        self.assertEqual(pending_tasks_1, ["tika"])
        youtube_tasks = self.youtube.get_pending_tasks()
        self.assertEqual(youtube_tasks, ["tika"])

    def test_get_secondary_pending_tasks(self):
        # Set Tika task as completed
        self.document_1.pipeline["tika"] = {"success": True}
        self.document_1.save()
        self.youtube.pipeline["tika"] = {"success": True}
        self.youtube.save()
        # Assert that tasks depending on Tika have become pending
        pending_tasks_1 = self.document_1.get_pending_tasks()
        self.assertEqual(pending_tasks_1, [])
        youtube_tasks = self.youtube.get_pending_tasks()
        self.assertEqual(youtube_tasks, ["extruct", "video_preview"])

    def test_reset_harvest_results(self):
        # Modify a document with some fake harvest data
        self.document_1.tasks = {
            "test": {
                "depends_on": ["$.url"],
                "checks": []
            }
        }
        self.document_1.derivatives = {"test": "test"}
        self.document_1.pipeline = {
            "test": {
                "success": True
            }
        }
        self.document_1.pending_at = now()
        # Reset and assert that correct defaults are in place
        self.document_1.reset_task_results()
        self.assertEqual(self.document_1.tasks, default_document_tasks())
        self.assertEqual(self.document_1.derivatives, {})
        self.assertEqual(self.document_1.pipeline, {})
        self.assertIsNone(self.document_1.pending_at)


class TestSimpleDispatchDocumentTasks(TestCase):

    dataset_version = None
    set = None
    documents = []
    document = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dataset_version, cls.set, cls.documents = create_file_document_set(
            "test",
            [{"url": "https://example.com/1"}, {"url": "https://example.com/2"}],
            [{"url": "https://example.com/1"}, {"url": "https://example.com/2", "status": 404}],
        )
        cls.success, cls.not_found = cls.documents

    @patch("files.models.resources.metadata.HttpTikaResource._send")
    def test_dispatch_document_tasks_synchronous(self, send_mock):
        dispatch_document_tasks("files", [doc.id for doc in self.documents], asynchronous=False)
        # Assert documents in general
        for doc in FileDocument.objects.all():
            self.assertEqual(doc.domain, "example.com")
            self.assertIsNone(doc.mime_type)
            self.assertEqual(doc.type, "unknown")
            self.assertIn("tika", doc.pipeline)
            self.assertIn("success", doc.pipeline["tika"])
        # Assert the success document
        success = FileDocument.objects.get(id=self.success.id)
        self.assertTrue(success.pipeline["tika"]["success"])
        self.assertIn("tika", success.derivatives)
        self.assertEqual(success.derivatives["tika"], {"texts": ["Tika content for https://example.com/1"]})
        self.assertFalse(success.is_not_found)
        self.assertIsNone(success.pending_at, "Expected Document to indicate it is no longer pending for tasks")
        self.assertEqual(success.get_pending_tasks(), [], "Expected simple tasks to complete, leaving no pending tasks")
        # Assert the not found document
        not_found = FileDocument.objects.get(id=self.not_found.id)
        self.assertFalse(not_found.pipeline["tika"]["success"])
        self.assertNotIn("tika", not_found.derivatives)
        self.assertTrue(not_found.is_not_found)
        self.assertFalse(not_found.pending_at, "Expected Document to indicate it is no longer pending for tasks")
        self.assertEqual(
            not_found.get_pending_tasks(), [],
            "Expected 404 to register no pending tasks until the pipeline field gets a reset"
        )