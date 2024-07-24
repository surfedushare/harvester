import logging

from django.conf import settings

from datagrowth.resources import HttpResource


logger = logging.getLogger("harvester")


class HvaPureResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["hva"]["endpoint"] + "/ws/api/research-outputs" \
        if settings.SOURCES["hva"]["endpoint"] else "/ws/api/research-outputs"

    def auth_headers(self):
        return {
            "api-key": settings.SOURCES["hva"]["api_key"]
        }

    def next_parameters(self):
        content_type, data = self.content
        count = data["count"]
        page_info = data["pageInformation"]
        offset = page_info["offset"]
        size = page_info["size"]
        remaining = count - (offset + size)
        if remaining <= 0:
            return {}
        return {
            "size": size,
            "offset": offset + size
        }

    class Meta:
        verbose_name = "HvA Pure harvest"
        verbose_name_plural = "HvA Pure harvests"
