from django.conf import settings

from datagrowth.resources import HttpResource


class SiaProjectIdsResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["sia"]["endpoint"] + "/v1/projecten"
    HEADERS = {
        "accept": "application/json"
    }

    def auth_headers(self):
        return {
            "Authorization": f"Bearer {settings.SOURCES['sia']['api_key']}"
        }

    class Meta:
        verbose_name = "SIA project ids harvest"
        verbose_name_plural = "SIA project ids harvests"


class SiaProjectDetailsResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["sia"]["endpoint"] + "/v1/projecten/{}"
    HEADERS = {
        "accept": "application/json"
    }

    @property
    def success(self):
        # We're allowing 403, because "deleted" projects will return this instead of 204 for unknown reasons.
        return super().success or self.status == 403

    def auth_headers(self):
        return {
            "Authorization": f"Bearer {settings.SOURCES['sia']['api_key']}"
        }

    class Meta:
        verbose_name = "SIA project detail harvest"
        verbose_name_plural = "SIA project detail harvests"
