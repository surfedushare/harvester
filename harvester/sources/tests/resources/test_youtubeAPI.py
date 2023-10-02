from django.test import TestCase
from unittest.mock import patch

from files.models import YoutubeAPIResource


class TestYoutubeAPIResource(TestCase):

    @patch("files.models.resources.youtube_api.YoutubeAPIResource._send")
    def test_regex(self, send_mock):
        urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=feedrec_grec_index",
            "http://www.youtube.com/v/dQw4w9WgXcQ?fs=1&amp;hl=en_US&amp;rel=0",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ#t=0m10s",
            "http://www.youtube.com/embed/dQw4w9WgXcQ?rel=0",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://youtu.be/dQw4w9WgXcQ"

        ]

        for url in urls:
            resource = YoutubeAPIResource().get(url, "videos")
            self.assertEqual(resource.request_without_auth()["url"],
                             "https://youtube.googleapis.com/youtube/v3/videos?id=dQw4w9WgXcQ&part=snippet%2Cplayer%2CcontentDetails%2Cstatus")
