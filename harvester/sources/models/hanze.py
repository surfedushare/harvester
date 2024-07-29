from django.conf import settings

from datagrowth.resources import HttpResource


class HanzeResearchObjectResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["hanze"]["endpoint"] + "/nppo/research-outputs" \
        if settings.SOURCES["hanze"]["endpoint"] else "/nppo/research-outputs"

    def send(self, method, *args, **kwargs):
        args = (args[1],)  # ignores set_specification input, we'll always use the default
        return super().send(method, *args, **kwargs)

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
