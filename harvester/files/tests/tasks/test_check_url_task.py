from django.test import TestCase

from datagrowth.resources.testing import EnableGlobalCacheMixin

from files.models import FileDocument
from files.tasks.metadata import check_url_task
from files.tests.factories import create_file_document_set


class TestCheckURLTask(EnableGlobalCacheMixin, TestCase):

    dataset_version = None
    set = None
    documents = []
    document = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dataset_version, cls.set, cls.documents = create_file_document_set(
            set_specification="test",
            docs=[{"url": "https://surf.nl"},
                  {"url": "https://surf.nl/does-not-exist"}],
            checks=[{"url": "https://surf.nl"},
                    {"url": "https://surf.nl/does-not-exist", "status": 404}]
        )
        cls.success, cls.fail, = cls.documents

    def test_task(self):
        check_url_task("files", [doc.id for doc in self.documents])
        for doc in FileDocument.objects.all():
            self.assertIn("check_url", doc.task_results)
            self.assertIn("success", doc.task_results["check_url"])
            self.assertTrue(doc.task_results["check_url"]["success"])
            self.assertIn("check_url", doc.derivatives)

        success = FileDocument.objects.get(id=self.success.id)
        fail = FileDocument.objects.get(id=self.fail.id)
        self.assertEqual(success.derivatives["check_url"], {
            "url": "https://surf.nl",
            "status": 200,
            "content_type": "text/html",
            "has_redirect": False,
            "has_temporary_redirect": False
        })
        self.assertFalse(success.is_not_found)
        self.assertEqual(fail.derivatives["check_url"], {
            "url": "https://surf.nl/does-not-exist",
            "status": 404,
            "content_type": "text/html",
            "has_redirect": False,
            "has_temporary_redirect": False
        })
        self.assertTrue(fail.is_not_found)
