import re

from datagrowth.resources import HttpResource
from django.conf import settings


class YoutubeAPIResource(HttpResource):

    url_regex = re.compile(r".*(?:youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=)([^#\&\?]*).*", re.IGNORECASE)

    URI_TEMPLATE = \
        "https://youtube.googleapis.com/youtube/v3/videos?part=snippet,player&" \
        "id=" + "{}"

    def url_to_id(self, url: str):
        url_match = self.url_regex.findall(url)
        return url_match[0]

    def auth_parameters(self):
        return {"key": settings.GOOGLE_API_KEY}

    def variables(self, *args):
        vars = super().variables(*args)
        vars["url"] = map(self.url_to_id, vars["url"])
        print(vars)
        return vars
