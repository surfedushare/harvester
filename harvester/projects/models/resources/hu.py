from django.conf import settings

from datagrowth.resources import HttpResource


class HuProjectResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["hu"]["endpoint"] + "/api/publinova/projects" \
        if settings.SOURCES["hu"]["endpoint"] else "/api/publinova/projects"

    def auth_headers(self):
        return {
            "apiKey": settings.SOURCES["hu"]["api_key"]
        }
