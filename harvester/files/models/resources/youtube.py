import os
import re
from copy import copy
from io import BytesIO
from urllib.parse import urlparse, urljoin

from django.conf import settings

from versatileimagefield.fields import VersatileImageField
from versatileimagefield.utils import build_versatileimagefield_url_set

from datagrowth.resources import HttpResource, HttpFileResource


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


class YoutubeThumbnailResource(HttpFileResource):

    preview = VersatileImageField(upload_to=os.path.join("files", "previews", "youtube"), null=True, blank=True)

    @staticmethod
    def get_preview_filename(thumbnail_url):
        url = urlparse(thumbnail_url)
        path = url.path
        remainder, filename = os.path.split(path)
        remainder, youtube_id = os.path.split(remainder)
        return f"{youtube_id}-{filename}"

    def _update_from_results(self, response):
        # Save the metadata
        self.head = dict(response.headers.lower_items())
        self.status = response.status_code
        # Get the image file we want to save
        fd = BytesIO(response.content)
        # Defer a file name from the URL
        variables = self.variables()
        preview_file_name = self.get_preview_filename(variables["url"][0])
        # Save to instance
        self.preview.save(preview_file_name, fd)

    @property
    def content(self):
        if self.success:
            signed_urls = build_versatileimagefield_url_set(self.preview, [
                ('full_size', 'url'),
                ('preview', 'thumbnail__400x300'),
                ('preview_small', 'thumbnail__200x150'),
            ])
            return "application/json", {
                image_key: urljoin(url, urlparse(url).path)
                for image_key, url in signed_urls.items()
            }
        return None, None
