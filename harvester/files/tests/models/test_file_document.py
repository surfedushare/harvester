from copy import deepcopy

from django.test import TestCase

from files.models import FileDocument


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
        # Complete the check_url task by patching it and see if secondary tasks trigger
        file_document.pipeline["check_url"] = check_url_pipeline
        file_document.derivatives["check_url"] = check_url_derivative
        self.assertEqual(file_document.get_pending_tasks(), ["tika"])
        self.assertIsNotNone(file_document.pending_at)
        self.assertIsNone(file_document.finished_at)
