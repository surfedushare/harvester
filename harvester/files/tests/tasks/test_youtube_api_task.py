from django.test import TestCase
from unittest.mock import patch

from datagrowth.configuration import register_defaults

from files.models import FileDocument
from files.tasks.metadata import youtube_api_task
from files.tests.factories import create_file_document_set


class TestYoutubeAPITask(TestCase):

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
            set_specification="test",
            docs=[{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
                  {"url": "https://www.youtube.com/watch?v=3kwDVw0u4Kw"}],
            tikas=None,
            youtubes=[{"id": "dQw4w9WgXcQ", "type": "videos"},
                      {"id": "wrongIdHere", "type": "videos"}]
        )
        cls.success, cls.fail, = cls.documents

    @classmethod
    def tearDownClass(cls):
        register_defaults("global", {
            "cache_only": False
        })
        super().tearDownClass()

    @patch("files.models.resources.youtube_api.YoutubeAPIResource._send")
    def test_embed_url(self, send_mock):
        youtube_api_task("files", [doc.id for doc in self.documents])
        for doc in FileDocument.objects.all():
            self.assertIn("youtube_api", doc.pipeline)
            self.assertIn("success", doc.pipeline["youtube_api"])
        # Assert the success document
        success = FileDocument.objects.get(id=self.success.id)
        self.assertTrue(success.pipeline["youtube_api"]["success"])
        self.assertIn("youtube_api", success.derivatives)
        self.assertEqual(success.derivatives["youtube_api"],
                         {'license': 'youtube',
                          'duration': 'PT3M33S',
                          'previews': {
                              'preview': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
                              'full_size': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
                              'preview_small': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg'
                          },
                          'embed_url': 'www.youtube.com/embed/dQw4w9WgXcQ',
                          'definition': 'hd',
                          'description': 'this is a description'})
        self.assertFalse(success.is_not_found)
