from django.conf import settings

from datagrowth.resources import HttpResource


class FontysOrganizationResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["fontys"]["endpoint"] + "/ws/api/organizational-units" \
        if settings.SOURCES["fontys"]["endpoint"] else "/ws/api/organizational-units"

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
        verbose_name = "Fontys organization resource"
        verbose_name_plural = "Fontys organization resources"
