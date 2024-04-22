from copy import deepcopy

from django.test import TestCase

from files.models import FileDocument, CheckURLResource, HttpTikaResource


class FileDocumentTestCase(TestCase):

    fixtures = ["test-file-document.json"]

    def test_get_pending_tasks_hash_update(self):
        # Check that file from fixture is not processing
        file_document = FileDocument.objects.get(pk=1)
        check_url_pipeline = deepcopy(file_document.pipeline["check_url"])
        check_url_derivative = deepcopy(file_document.derivatives["check_url"])
        self.assertEqual(file_document.get_pending_tasks(), [])
        # Change the hash and see if the file becomes processing
        file_document.update({"hash": "abc123"})
        self.assertEqual(file_document.get_pending_tasks(), ["check_url"])
        self.assertIsNotNone(file_document.pending_at)
        self.assertIsNone(file_document.finished_at)
        # The Tika and URL resources should be cleared
        self.assertEqual(CheckURLResource.objects.count(), 1, "Expected check_url resource for file to get purged")
        self.assertEqual(HttpTikaResource.objects.count(), 1, "Expected tika resources for file to get purged")
        # Complete the check_url task by patching it and see if secondary tasks trigger
        file_document.pipeline["check_url"] = check_url_pipeline
        file_document.derivatives["check_url"] = check_url_derivative
        self.assertEqual(file_document.get_pending_tasks(), ["tika"])
        self.assertIsNotNone(file_document.pending_at)
        self.assertIsNone(file_document.finished_at)

    def test_invalidate_task_resource_purge(self):
        # Pre-test asserts
        self.assertEqual(CheckURLResource.objects.count(), 2, "Expected two check_url resources at start of test")
        self.assertEqual(HttpTikaResource.objects.count(), 2, "Expected two tika resources at start of test")
        file_document = FileDocument.objects.get(pk=1)
        file_document.invalidate_task("check_url")
        self.assertIsNotNone(file_document.pending_at)
        self.assertIsNone(file_document.finished_at)
        self.assertEqual(CheckURLResource.objects.count(), 1, "Expected check_url resource from pipeline to be deleted")
        self.assertEqual(HttpTikaResource.objects.count(), 2, "Expected tika resources to be unaffected")
