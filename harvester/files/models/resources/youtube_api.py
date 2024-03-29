import re
from copy import copy

from django.conf import settings

from datagrowth.resources import HttpResource


class YoutubeAPIResource(HttpResource):

    url_regex = re.compile(r".*(?:youtu.be\/|v\/|u\/\w\/|embed\/|watch\?.*v=)([^#\&\?]*).*", re.IGNORECASE)

    URI_TEMPLATE = \
        "https://youtube.googleapis.com/youtube/v3/{}"

    HEADERS = {
        "Referer": f"https://{settings.DOMAIN}"
    }

    def handle_errors(self):
        content_type, data = self.content
        if data and not len(data['items']):
            self.status = 404
        return super().handle_errors()

    @classmethod
    def url_to_id(cls, url: str):
        url_match = cls.url_regex.findall(url)
        return url_match[0] if url_match else None

    def auth_parameters(self):
        return {"key": settings.GOOGLE_API_KEY}

    def variables(self, *args):
        return {
            "video_id": self.url_to_id(args[0]),
            "url": [args[1]],
            "kind": args[1]
        }

    def parameters(self, video_id, kind, **kwargs):
        parameters = copy(self.PARAMETERS)
        parameters["id"] = video_id
        if kind == "videos":
            parameters["part"] = "snippet,player,contentDetails,status"
        elif kind == "caption":
            parameters["part"] = "snippet"
        return parameters
