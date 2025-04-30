from django.conf import settings

from datagrowth.resources import HttpResource


class HuPersonResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["hu"]["endpoint"] + "/api/publinova/persons" \
        if settings.SOURCES["hu"]["endpoint"] else "/api/publinova/persons"

    def auth_headers(self):
        return {
            "apiKey": settings.SOURCES["hu"]["api_key"]
        }

    class Meta:
        verbose_name = "HU person harvest"
        verbose_name_plural = "HU person harvests"
