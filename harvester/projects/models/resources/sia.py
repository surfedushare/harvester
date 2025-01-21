from datetime import datetime

from django.conf import settings

from datagrowth.resources import HttpResource


class SiaProjectIdsResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["sia"]["endpoint"] + "/v1/projecten?updatessinds={}"
    HEADERS = {
        "accept": "application/json"
    }

    def variables(self, *args):
        # We need to parse ISO inputs to SIA's own special datetime format.
        # Parse variables as normal and use variables used to fill in the URI_TEMPLATE.
        variables = super().variables(*args)
        url_variables = variables["url"]
        # If we don't receive datetime data from inputs we use 1970-01-01 as default harvesting start date.
        try:
            iso_updated_sinds = url_variables[1]
        except IndexError:
            iso_updated_sinds = "1970-01-01T01:20:38Z"
        # Transform the ISO standard into SIA's special format
        updated_since = datetime.fromisoformat(iso_updated_sinds.replace('Z', '+00:00'))
        return {
            "url": [updated_since.strftime("%Y%m%d%H%M%S")]  # see SIA documentation about format
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
