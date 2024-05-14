import logging

from django.conf import settings
from django.db import models

from core.models import HarvestHttpResource


logger = logging.getLogger("harvester")


class HkuMetadataResource(HarvestHttpResource):

    set_specification = models.CharField(max_length=255, blank=True, null=False, default="hku")
    use_multiple_sets = False

    URI_TEMPLATE = settings.SOURCES["hku"]["endpoint"] + "/octo/repository/api2/getResults" \
        if settings.SOURCES["hku"]["endpoint"] else "/octo/repository/api2/getResults"

    PARAMETERS = {
        "format": "json",
        "project": "pubplatv4"
    }

    def handle_errors(self):
        super().handle_errors()
        if not self.body:
            self.status = 204

    class Meta:
        verbose_name = "HKU metadata harvest"
        verbose_name_plural = "HKU metadata harvests"
