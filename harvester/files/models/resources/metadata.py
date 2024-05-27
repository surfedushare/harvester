import logging
import json
from urllib3.exceptions import LocationParseError
from requests.exceptions import InvalidURL

from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType

from datagrowth.resources import HttpResource, URLResource
import extruct


logger = logging.getLogger("harvester")


class HttpTikaResourceBase(HttpResource):

    URI_TEMPLATE = settings.TIKA_HOST + "/rmeta/text?fetchKey={}"
    PARAMETERS = {
        "fetcherName": "http"
    }

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

    class Meta:
        abstract = True


class ExtructResourceBase(URLResource):

    @property
    def success(self):
        success = super().success
        content_type, data = self.content
        return success and bool(data)

    @property
    def content(self):
        if super().success:
            content_type = self.head.get("content-type", "unknown/unknown").split(';')[0]
            if content_type != "text/html":
                return None, None
            try:
                result = extruct.extract(self.body)
                return "application/json", result
            except json.JSONDecodeError:
                pass
        return None, None

    class Meta:
        abstract = True


class HttpTikaResource(HttpTikaResourceBase):

    retainer_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE, related_name="+")

    @property
    def URI_TEMPLATE(self):
        return f"{settings.TIKA_HOST}/rmeta/{self.config.tika_return_type}"

    def variables(self, *args):
        return {
            "url": [],
            "fetch_key": args[0]
        }

    def parameters(self, fetch_key, **kwargs):
        params = super().parameters(**kwargs)
        params["fetchKey"] = fetch_key
        return params

    def _create_url(self, *args):
        # All input links are expected to be normalized to + through BaseExtractor.parse_url.
        # Here we double encode the + to %20 and Tika will decode twice which means we end up with %20 inside Tika.
        # Having spaces or + inside Tika server will lead to illegal character exceptions.
        url = super()._create_url(*args)
        return url.replace("+", "%252520")

    class Meta:
        app_label = "files"


class ExtructResource(ExtructResourceBase):

    retainer_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE, related_name="+")

    class Meta:
        app_label = "files"


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
