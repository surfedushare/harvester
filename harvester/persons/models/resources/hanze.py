from django.conf import settings

from datagrowth.resources import HttpResource


class HanzePersonResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["hanze"]["endpoint"] + "/nppo/persons" \
        if settings.SOURCES["hanze"]["endpoint"] else "/nppo/persons"

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


class HanzeUserResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["hanze"]["endpoint"] + "/nppo/users/{}" \
        if settings.SOURCES["hanze"]["endpoint"] else "/nppo/users/{}"

    def auth_headers(self):
        return {
            "Ocp-Apim-Subscription-Key": settings.SOURCES["hanze"]["api_key"]
        }
