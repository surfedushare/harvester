from copy import deepcopy

from django.test import TestCase

from files.models import Set, FileDocument, CheckURLResource, HttpTikaResource


class FileDocumentTestCase(TestCase):

    fixtures = ["test-file-document.json"]

    def test_get_pending_tasks_hash_update(self):
        # Load test data from fixture
        file_document = FileDocument.objects.get(pk=1)
        check_url_resource_id = file_document.task_results["check_url"]["id"]
        tika_resource_id = file_document.task_results["tika"]["id"]
        # Check that file from fixture is not processing
        check_url_task_results = deepcopy(file_document.task_results["check_url"])
        check_url_derivative = deepcopy(file_document.derivatives["check_url"])
        self.assertEqual(file_document.get_pending_tasks(), [])
        # Change the hash and see if the file becomes processing
        file_document.update({"hash": "abc123"})
        self.assertEqual(file_document.get_pending_tasks(), ["check_url"])
        self.assertIsNotNone(file_document.pending_at)
        self.assertIsNone(file_document.finished_at)
        # The Tika and URL resources should be cleared
        self.assertEqual(
            CheckURLResource.objects.filter(id=check_url_resource_id).count(), 0,
            "Expected check_url resource for file to get purged"
        )
        self.assertEqual(
            HttpTikaResource.objects.filter(id=tika_resource_id).count(), 0,
            "Expected tika resources for file to get purged"
        )
        # Complete the check_url task by patching it and see if secondary tasks trigger
        file_document.task_results["check_url"] = check_url_task_results
        file_document.derivatives["check_url"] = check_url_derivative
        self.assertEqual(file_document.get_pending_tasks(), ["tika"])
        self.assertIsNotNone(file_document.pending_at)
        self.assertIsNone(file_document.finished_at)

    def test_invalidate_task_resource_purge(self):
        # Pre-test asserts
        self.assertEqual(CheckURLResource.objects.count(), 3, "Expected three check_url resources at start of test")
        self.assertEqual(HttpTikaResource.objects.count(), 2, "Expected two tika resources at start of test")
        file_document = FileDocument.objects.get(pk=1)
        check_url_resource_id = file_document.task_results["check_url"]["id"]
        file_document.invalidate_task("check_url")
        self.assertIsNotNone(file_document.pending_at)
        self.assertIsNone(file_document.finished_at)
        self.assertEqual(
            CheckURLResource.objects.filter(id=check_url_resource_id).count(), 0,
            "Expected check_url resource from task results to be deleted"
        )
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
