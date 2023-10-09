import re
from copy import copy

from datagrowth.resources import HttpResource
from django.conf import settings


class YoutubeAPIResource(HttpResource):

    url_regex = re.compile(r".*(?:youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=)([^#\&\?]*).*", re.IGNORECASE)

    URI_TEMPLATE = \
        "https://youtube.googleapis.com/youtube/v3/{}"

    def url_to_id(self, url: str):
        url_match = self.url_regex.findall(url)
        return url_match[0]

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
