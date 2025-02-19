from django.conf import settings

from datagrowth.resources import HttpResource


class HanzePureProjectResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["hanze"]["endpoint"] + "/nppo/projects" \
        if settings.SOURCES["hanze"]["endpoint"] else "/nppo/projects"

    def auth_headers(self):
        return {
            "Ocp-Apim-Subscription-Key": settings.SOURCES["hanze"]["api_key"]
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
        verbose_name = "Hanze Pure project"
        verbose_name_plural = "Hanze Pure projects"
