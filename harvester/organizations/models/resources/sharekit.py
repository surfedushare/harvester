from urlobject import URLObject

from django.conf import settings

from datagrowth.resources import HttpResource


class SharekitOrganizationResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["sharekit"]["endpoint"] + "/api/jsonapi/channel/v1/{}/institutes"
    PARAMETERS = {
        "page[size]": 25
    }

    def auth_headers(self):
        return {
            "Authorization": f"Bearer {settings.SOURCES["sharekit"]["api_key"]}"
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
