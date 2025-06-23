import os
from urllib3.util import parse_url
from urllib.parse import quote_plus

from django.conf import settings

from datagrowth.resources import HttpFileResource


class MirrorFileResource(HttpFileResource):

    @staticmethod
    def is_url_supported(url: str) -> bool:
        scheme, auth, host, port, path, query, fragment = parse_url(url)
        return host.endswith("hanze.nl") or host.endswith("hva.nl")

    def auth_headers(self):
        scheme, auth, host, port, path, query, fragment = parse_url(self.request["url"])
        if host.endswith("hanze.nl"):
            return {
                "Ocp-Apim-Subscription-Key": settings.SOURCES["hanze"]["api_key"]
            }
        elif host.endswith("hva.nl"):
            return {
                "api-key": settings.SOURCES["hva"]["api_key"]
            }
        else:
            raise ValueError(f"Unknown hostname for MirrorFileResource: {host}")

    @property
    def content(self):
        if not self.success:
            return super().content
        # Instead of outputting the file with a Python object we return where to find to file through Django mechanisms.
        # On localhost it will be the media folder, but on AWS it will be an S3 bucket.
        return "application/json", {
            "public_url": os.path.join(settings.MEDIA_URL, quote_plus(self.body, safe="/"))
        }
