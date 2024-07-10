import logging
from urlobject import URLObject

from django.conf import settings

from datagrowth.resources import HttpResource


logger = logging.getLogger("harvester")


class PublinovaMetadataResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["publinova"]["endpoint"] + "/sources/products" \
        if settings.SOURCES["publinova"]["endpoint"] else "/sources/products"

    def auth_headers(self):
        return {
            "Authorization": f"Bearer {settings.SOURCES['publinova']['api_key']}"
        }

    def next_parameters(self):
        content_type, data = self.content
        next_link = data["links"].get("next", None)
        if not next_link:
            return {}
        next_url = URLObject(next_link)
        return {
            "page": next_url.query_dict["page"]
        }

    class Meta:
        verbose_name = "Publinova harvest"
        verbose_name_plural = "Publinova harvests"
