import logging
import json
from urllib3.exceptions import LocationParseError
from requests.exceptions import InvalidURL

from django.conf import settings

from datagrowth.resources import HttpResource, URLResource


logger = logging.getLogger("harvester")


class HttpTikaResource(HttpResource):

    @property
    def URI_TEMPLATE(self):
        return f"{settings.TIKA_HOST}/rmeta/{self.config.tika_return_type}"

    PARAMETERS = {
        "fetcherName": "http"
    }

    def variables(self, *args):
        return {
            "url": [],
            "fetch_key": args[0]
        }

    def parameters(self, fetch_key, **kwargs):
        params = super().parameters(**kwargs)
        # All input links are expected to be normalized to + through BaseExtractor.parse_url.
        # Here we double encode the + to %20 and Tika will decode twice which means we end up with %20 inside Tika.
        # Having spaces or + inside Tika server will lead to illegal character exceptions.
        params["fetchKey"] = fetch_key.replace("+", "%252520")
        return params

    def handle_errors(self):
        super().handle_errors()
        _, data = self.content
        has_content = False
        has_exception = False

        if data:
            first_tika_result = data[0]
            has_content = first_tika_result.get("X-TIKA:content", None)
            has_exception = len(
                dict(filter(lambda item:  "X-TIKA:EXCEPTION:" in item[0], first_tika_result.items()))) > 0

        if has_content and has_exception:
            self.status = 200
        elif not has_content and not has_exception:
            self.status = 204
        elif not has_content and has_exception:
            self.status = 1


class CheckURLResource(URLResource):

    def _update_from_results(self, response):
        self.head = dict(response.headers.lower_items())
        self.status = response.status_code
        has_redirect = any((res.is_redirect for res in response.history))
        if has_redirect:
            has_temporary_redirect = any((not res.is_permanent_redirect for res in response.history))
        else:
            has_temporary_redirect = False
        response_info = {
            "has_redirect": has_redirect,
            "has_temporary_redirect": has_temporary_redirect,
            "url": response.url,
            "status": response.status_code,
            "content_type": self.head.get("content-type", "unknown/unknown").split(';')[0]
        }
        self.body = json.dumps(response_info)

    def _send(self):
        try:
            super()._send()
        except (InvalidURL, LocationParseError):
            self.set_error(400, connection_error=True)

    @property
    def success(self):
        return bool(self.head)

    @property
    def content(self):
        info = json.loads(self.body) if self.body else None
        return "application/json", info  # application/json allows ExtractorProcessor to access info as a dict
