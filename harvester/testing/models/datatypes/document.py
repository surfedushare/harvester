from django.db import models

from datagrowth.resources.base import Resource

from core.models.datatypes import HarvestDocument, HarvestOverwrite
from files.models.resources.metadata import HttpTikaResource


def default_document_tasks():
    return {
        "tika": {
            "depends_on": ["$.url"],
            "checks": [],
            "resources": ["files.HttpTikaResource"]
        }
    }


class TestDocument(HarvestDocument):

    tasks = models.JSONField(default=default_document_tasks, blank=True)
    is_not_found = models.BooleanField(default=False)

    def apply_resource(self, resource: Resource):
        if isinstance(resource, HttpTikaResource):
            if resource.status == 404:
                self.is_not_found = True
                self.pending_at = None


class Overwrite(HarvestOverwrite):

    class Meta:
        verbose_name = "test overwrite"
        verbose_name_plural = "test overwrites"
