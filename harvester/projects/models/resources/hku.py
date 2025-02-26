import logging

from django.conf import settings

from datagrowth.resources import HttpResource


logger = logging.getLogger("harvester")


class HkuProjectResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["hku"]["endpoint"] + "/octo/repository/api2/getProjects" \
        if settings.SOURCES["hku"]["endpoint"] else "/octo/repository/api2/getProjects"

    PARAMETERS = {
        "format": "json",
        "project": "pubplatv4"
    }

    def handle_errors(self):
        super().handle_errors()
        if not self.body:
            self.status = 204
