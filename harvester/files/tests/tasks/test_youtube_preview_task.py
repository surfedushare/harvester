from django.test import TestCase

from datagrowth.resources.testing import EnableGlobalCacheMixin

from files.models import FileDocument
from files.tasks.previews import youtube_preview


class TestYoutubePreviewTask(EnableGlobalCacheMixin, TestCase):

    fixtures = ["test-youtube-document"]

    def test_youtube_preview(self):
        youtube_preview("files", [1])
        success = FileDocument.objects.get(id=1)
        self.assertTrue(success.task_results["youtube_preview"]["success"])
        self.assertIn("youtube_preview", success.derivatives)
        self.assertEqual(success.derivatives["youtube_preview"], {
            "preview": "/media/harvester/thumbnails/files/previews/youtube/dQw4w9WgXcQ-maxresdefault-thumbnail-400x300-70.jpg",  # noqa: E501
            "full_size": "/media/harvester/files/previews/youtube/dQw4w9WgXcQ-maxresdefault.jpg",
            "preview_small": "/media/harvester/thumbnails/files/previews/youtube/dQw4w9WgXcQ-maxresdefault-thumbnail-200x150-70.jpg",  # noqa: E501
        })
        self.assertFalse(success.is_not_found)
