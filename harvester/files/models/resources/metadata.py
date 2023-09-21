import logging
from json import JSONDecodeError

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
            except JSONDecodeError:
                pass
        return None, None

    class Meta:
        abstract = True


class HttpTikaResource(HttpTikaResourceBase):

    retainer_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE, related_name="+")

    class Meta:
        app_label = "files"


class ExtructResource(ExtructResourceBase):

    retainer_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE, related_name="+")

    class Meta:
        app_label = "files"
