from urlobject import URLObject

from datagrowth.resources import HttpResource
from core.models.resources.harvest import HarvestHttpResource


class MockHarvestResource(HarvestHttpResource):
    is_extracted = None  # legacy field which will disappear so we exclude it here

    URI_TEMPLATE = "http://localhost:8888/mocks/entity/{}"

    PARAMETERS = {
        "size": 20,
        "page_size": 10
    }

    def next_parameters(self):
        if not self.success or self.request["args"][0] == "merge":
            return {}
        content_type, data = self.content
        next_link = data.get("next", None)
        if not next_link:
            return {}
        next_url = URLObject(next_link)
        return {
            "page": next_url.query_dict["page"]
        }


class MockDetailResource(HttpResource):

    URI_TEMPLATE = "http://localhost:8888/mocks/entity/{}/{}"

    PARAMETERS = {
        "size": 20,
        "page_size": 10
    }
