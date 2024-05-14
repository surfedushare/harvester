from copy import deepcopy

from django.test import TestCase

from files.models import Set, FileDocument, CheckURLResource, HttpTikaResource


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

    def test_clean_url(self):
        valid_url = "https://www.example.com"
        collection = Set()
        doc = FileDocument.build({"url": valid_url, "external_id": "abc123", "set": "test"}, collection=collection)
        doc.clean()
        self.assertFalse(doc.is_not_found, "Expected valid URL to be marked as 'found' by default")
        invalid_urls = [
            "htp://example.com",  # Incorrect scheme
            "http:///example.com",  # Missing host
            "://example.com",  # Missing scheme
            "www.example.com",  # Missing scheme and leading slashes
            "http://Handreiking+voor+professionals+in+de+geboorte-+en+jeugdgezondheidszorg",
            "https://www⁠.bd⁠.nl⁠/dongen⁠/hoe-de-bus-verdween-uit-jorwerd-openbaar-vervoerarmoede~a9818109⁠/",
            None
        ]
        for invalid_url in invalid_urls:
            doc = FileDocument.build(
                {"url": invalid_url, "external_id": "abc123", "set": "test"},
                collection=collection
            )
            doc.clean()
            self.assertTrue(doc.is_not_found, f"Expected invalid URL to be marked as 'not found': {invalid_url}")
