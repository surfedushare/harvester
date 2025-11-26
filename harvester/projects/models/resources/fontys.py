import logging

from django.conf import settings

from datagrowth.resources import HttpResource


logger = logging.getLogger("harvester")


class FontysPureProjectResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["fontys"]["endpoint"] + "/ws/api/projects" \
        if settings.SOURCES["fontys"]["endpoint"] else "/ws/api/projects"

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
        verbose_name = "Fontys Pure project"
        verbose_name_plural = "Fontys Pure projects"
