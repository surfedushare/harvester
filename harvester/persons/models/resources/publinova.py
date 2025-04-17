import logging
from urlobject import URLObject

from django.conf import settings

from datagrowth.resources import HttpResource


logger = logging.getLogger("harvester")


class PublinovaPersonResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["publinova"]["endpoint"] + "/sources/people" \
        if settings.SOURCES["publinova"]["endpoint"] else "/sources/people"

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
        verbose_name = "Publinova person harvest"
        verbose_name_plural = "Publinova person harvests"
