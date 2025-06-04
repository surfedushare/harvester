from django.test import TestCase

from datagrowth.resources.testing import EnableGlobalCacheMixin

from files.models import FileDocument
from files.tasks.metadata import publish_content_task


class TestPublishContentTask(EnableGlobalCacheMixin, TestCase):

    fixtures = ["test-file-document"]

    def test_task(self):
        test_documents = FileDocument.objects.filter(id__in=[1, 2])
        publish_content_task("files", [doc.id for doc in test_documents])
        # Test document where mirrors aren't necessary
        auto_success = FileDocument.objects.get(id=1)
        self.assertEqual(auto_success.task_results["publish_content"], {"success": True, "is_auto_succeed": True})
        self.assertEqual(auto_success.derivatives["publish_content"], {
            "public_url": "https://api.surfsharekit.nl/api/v1/files/repoItemFiles/dc11453f-df4a-4a32-a927-a61512d4cd26",
        })
        # Test document where mirroring should have taken place
        mirror_success = FileDocument.objects.get(id=2)
        self.assertIn("success", mirror_success.task_results["publish_content"])
        self.assertTrue(mirror_success.task_results["publish_content"]["success"])
        self.assertEqual(mirror_success.derivatives["publish_content"], {
            "public_url": "/media/harvester/files/downloads/5/f5/20250514105202066903.EPRIME_D2.1_Pre-school_and_primary_school_PE_teachers_needs_and_assets_analysis_report.pdf",  # noqa: E501
        })
