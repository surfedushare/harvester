import logging

from django.conf import settings

from datagrowth.resources import HttpResource


logger = logging.getLogger("harvester")


class HvaPersonResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["hva"]["endpoint"] + "/ws/api/persons" \
        if settings.SOURCES["hva"]["endpoint"] else "/ws/api/persons"

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
        verbose_name = "HvA person resource"
        verbose_name_plural = "HvA person resources"


class HvAUserResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["hva"]["endpoint"] + "/ws/api/users/{}" \
        if settings.SOURCES["hva"]["endpoint"] else "/ws/api/users/{}"

    def auth_headers(self):
        return {
            "api-key": settings.SOURCES["hva"]["api_key"]
        }

    @property
    def content(self):
        content_type, data = super().content
        if data:
            data["uuid"] = self.request["args"][0]
        return content_type, data

    class Meta:
        verbose_name = "HvA user resource"
        verbose_name_plural = "HvA user resources"
