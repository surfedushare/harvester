import logging

from django.conf import settings
from django.db import models

from core.models import HarvestHttpResource


logger = logging.getLogger("harvester")


class HvaPureResource(HarvestHttpResource):

    set_specification = models.CharField(max_length=255, blank=True, null=False, default="hva")
    use_multiple_sets = False

    URI_TEMPLATE = settings.SOURCES["hva"]["endpoint"] + "/ws/api/research-outputs" \
        if settings.SOURCES["hva"]["endpoint"] else "/ws/api/research-outputs"

    def auth_headers(self):
        return {
            "api-key": settings.SOURCES["hva"]["api_key"]
        }

    def next_parameters(self):
        content_type, data = self.content
        count = data["count"]
        page_info = data["pageInformation"]
        offset = page_info["offset"]
        size = page_info["size"]
        remaining = count - (offset + size)
        if remaining <= 0:
            return {}
        return {
            "size": size,
            "offset": offset + size
        }

    class Meta:
        verbose_name = "HvA Pure harvest"
        verbose_name_plural = "HvA Pure harvests"
