import json

import datagrowth.exceptions
from django.test import TestCase
from unittest.mock import patch

from files.models import YoutubeAPIResource


class TestYoutubeAPIResource(TestCase):

    @patch("files.models.resources.youtube_api.YoutubeAPIResource._send")
    def test_regex(self, send_mock):
        urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=feedrec_grec_index",
            "https://www.youtube.com/v/dQw4w9WgXcQ?fs=1&amp;hl=en_US&amp;rel=0",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ#t=0m10s",
            "https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/watch?annotation_id=annotation_123&feature=iv&src_vid=oI5-Cl-jvSs&v=dQw4w9WgXcQ",
        ]

        for url in urls:
            resource = YoutubeAPIResource(
                body=json.dumps({"items": []}),
                head={"content-type": "application/json"},
                status=200,
            ).get(url, "videos")
            self.assertEqual(resource.request_without_auth()["url"],
                             "https://youtube.googleapis.com/youtube/v3/"
                             "videos?id=dQw4w9WgXcQ&part=snippet%2Cplayer%2CcontentDetails%2Cstatus")

    def test_handle_errors_no_items(self):
        resource = YoutubeAPIResource(
            body=json.dumps({"items": []}),
            head={"content-type": "application/json"},
            status=200,
        )
        self.assertRaises(datagrowth.exceptions.DGHttpError40X, resource.handle_errors)
        self.assertFalse(resource.success)
        self.assertEqual(resource.status, 404)

    def test_handle_errors_forbidden(self):
        resource = YoutubeAPIResource(
            body="",
            head={"content-type": "application/json"},
            status=403,
        )
        self.assertRaises(datagrowth.exceptions.DGHttpError40X, resource.handle_errors)
        self.assertFalse(resource.success)
        self.assertEqual(resource.status, 403)
