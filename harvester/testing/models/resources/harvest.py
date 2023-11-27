from urllib.parse import urlparse, parse_qs

from datagrowth.resources import TestClientResource


class MockHarvestResource(TestClientResource):

    test_view_name = "testing:entities"

    PARAMETERS = {
        "size": 20,
        "page_size": 10
    }

    def next_parameters(self):
        content_type, data = self.content
        if not data or not (next_url := data.get("next")):
            return {}
        next_link = urlparse(next_url)
        params = parse_qs(next_link.query)
        return {
            "page": params["page"]
        }


class MockIdsResource(TestClientResource):
    test_view_name = "testing:entity-ids"


class MockDetailResource(TestClientResource):

    test_view_name = "testing:entity-details"

    PARAMETERS = {
        "size": 20,
        "page_size": 10
    }
