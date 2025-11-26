import logging

from django.conf import settings

from datagrowth.resources import HttpResource


logger = logging.getLogger("harvester")


class FontysPersonResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["fontys"]["endpoint"] + "/ws/api/persons" \
        if settings.SOURCES["fontys"]["endpoint"] else "/ws/api/persons"

    def auth_headers(self):
        return {
            "api-key": settings.SOURCES["fontys"]["api_key"]
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
        verbose_name = "Fontys person resource"
        verbose_name_plural = "Fontys person resources"
