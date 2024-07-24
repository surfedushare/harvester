import logging

from django.conf import settings

from datagrowth.resources import HttpResource


logger = logging.getLogger("harvester")


class BuasPureResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["buas"]["endpoint"] + "/ws/api/524/research-outputs" \
        if settings.SOURCES["buas"]["endpoint"] else "/ws/api/524/research-outputs"

    HEADERS = {
        "accept": "application/json"
    }

    def auth_headers(self):
        return {
            "api-key": settings.SOURCES["buas"]["api_key"]
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
        verbose_name = "BUAS Pure harvest"
        verbose_name_plural = "BUAS Pure harvests"
