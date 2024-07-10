from urlobject import URLObject

from django.conf import settings

from datagrowth.resources import HttpResource


class SharekitMetadataHarvest(HttpResource):

    URI_TEMPLATE = settings.SHAREKIT_BASE_URL + "/api/jsonapi/channel/v1/{}/repoItems?filter[modified][GE]={}"
    PARAMETERS = {
        "page[size]": 25
    }

    def auth_headers(self):
        return {
            "Authorization": f"Bearer {settings.SHAREKIT_API_KEY}"
        }

    def next_parameters(self):
        content_type, data = self.content
        next_link = data["links"].get("next", None)
        if not next_link:
            return {}
        next_url = URLObject(next_link)
        return {
            "page[number]": next_url.query_dict["page[number]"]
        }

    def handle_errors(self):
        content_type, data = self.content
        if data and not len(data.get("data", [])):
            self.status = 204

    class Meta:
        verbose_name = "Sharekit metadata harvest"
        verbose_name_plural = "Sharekit metadata harvest"
