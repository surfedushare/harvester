from unittest.mock import patch

from django.test import TestCase

from datagrowth.configuration import register_defaults
from core.tasks import dispatch_document_tasks, cancel_document_tasks
from files.tests.factories import create_file_document_set
from files.models import FileDocument


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
            [
                {"url": "https://example.com/1"},
                {"url": "https://example.com/2", "access_rights": "RestrictedAccess", "copyright": "yes"},
                {"url": "https://youtu.be/3"}
            ],
        )
        cls.document_1, cls.document_2, cls.youtube = cls.documents

    def test_get_primary_pending_tasks(self):
        pending_tasks_1 = self.document_1.get_pending_tasks()
        self.assertEqual(pending_tasks_1, ["check_url"])
        youtube_tasks = self.youtube.get_pending_tasks()
        self.assertEqual(youtube_tasks, ['video_preview', 'youtube_api'])

    def test_get_secondary_pending_tasks(self):
        # Set Tika task as completed
        self.document_1.pipeline["check_url"] = {"success": True}
        self.document_1.derivatives["check_url"] = {"status": 200}
        self.document_1.save()
        self.youtube.pipeline["youtube_api"] = {"success": True}
        self.youtube.pipeline["video_preview"] = {"success": True}
        self.youtube.save()
        # Assert that tasks depending on Tika have become pending
        pending_tasks_1 = self.document_1.get_pending_tasks()
        self.assertEqual(pending_tasks_1, ["tika"])
        youtube_tasks = self.youtube.get_pending_tasks()
        self.assertEqual(youtube_tasks, [])

    def test_get_analysis_disallowed(self):
        pending_tasks_2 = self.document_2.get_pending_tasks()
        self.assertEqual(pending_tasks_2, [], "Expected no tasks to execute when analysis is disallowed")


class TestSimpleDocumentTasks(TestCase):

    dataset_version = None
    set = None
    documents = []
    document = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        register_defaults("global", {
            "cache_only": True
        })
        cls.dataset_version, cls.set, cls.documents = create_file_document_set(
            "test",
            [{"url": "https://example.com/1"}, {"url": "https://example.com/2"}],
            tikas=[{"url": "https://example.com/1"}, {"url": "https://example.com/2", "status": 404}],
            checks=[{"url": "https://example.com/1", "status": 200}, {"url": "https://example.com/2", "status": 404}],
        )
        cls.success, cls.not_found = cls.documents

    @classmethod
    def tearDownClass(cls):
        register_defaults("global", {
            "cache_only": False
        })
        super().tearDownClass()

    @patch("files.models.resources.metadata.HttpTikaResource._send")
    def test_dispatch_document_tasks_synchronous(self, send_mock):
        dispatch_document_tasks("files", [doc.id for doc in self.documents], asynchronous=False)
        dispatch_document_tasks("files", [doc.id for doc in self.documents], asynchronous=False)
        # Assert documents in general
        for doc in FileDocument.objects.all():
            self.assertEqual(doc.domain, "example.com")
            self.assertIsNone(doc.mime_type)
            self.assertEqual(doc.type, "unknown")
            self.assertTrue(doc.pipeline["check_url"]["success"])
        # Assert the success document
        success = FileDocument.objects.get(id=self.success.id)
        self.assertIn("check_url", success.derivatives)
        self.assertEqual(success.derivatives["tika"], {"texts": ["Tika content for https://example.com/1"]})
        self.assertFalse(success.is_not_found)
        self.assertIsNone(success.pending_at, "Expected Document to indicate it is no longer pending for tasks")
        self.assertIsNotNone(success.finished_at, "Expected Document to indicate it is finished")
        self.assertEqual(success.get_pending_tasks(), [], "Expected simple tasks to complete, leaving no pending tasks")
        # Assert the not found document
        not_found = FileDocument.objects.get(id=self.not_found.id)
        self.assertNotIn("tika", not_found.pipeline)
        self.assertNotIn("tika", not_found.derivatives)
        self.assertTrue(not_found.is_not_found)
        self.assertFalse(not_found.pending_at, "Expected Document to indicate it is no longer pending for tasks")
        self.assertIsNotNone(not_found.finished_at, "Expected Document to indicate it is finished")
        self.assertEqual(
            not_found.get_pending_tasks(), [],
            "Expected 404 to register no pending tasks until the pipeline field gets a reset"
        )

    def test_dispatch_document_tasks_no_documents(self):
        dispatch_document_tasks("files", [], asynchronous=False)

    def test_cancel_document_tasks(self):
        cancel_document_tasks("files", self.documents)
        for doc in FileDocument.objects.all():
            self.assertNotEqual(doc.pipeline, {}, "Expected cancel_document_tasks to write to pipeline")
            for task, result in doc.pipeline.items():
                self.assertEqual(result, {"success": False, "canceled": True})

    def test_cancel_document_tasks_no_documents(self):
        cancel_document_tasks("files", [])
        self.assertGreater(FileDocument.objects.all().count(), 0)
        for doc in FileDocument.objects.all():
            self.assertEqual(doc.pipeline, {}, "Expected cancel_document_tasks to do nothing without input documents")
