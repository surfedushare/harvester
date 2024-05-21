from django.db import models
from django.utils.timezone import now

from datagrowth.resources.base import Resource

from core.models.datatypes import HarvestDocument, HarvestOverwrite
from files.models.resources.metadata import CheckURLResource
from files.models.datatypes.file import Redirects
from testing.constants import SEED_DEFAULTS


def default_document_tasks():
    return {
        "check_url": {
            "depends_on": ["$.url"],
            "checks": [],
            "resources": ["files.CheckURLResource"]
        },
        "tika": {
            "depends_on": ["check_url"],
            "checks": [],
            "resources": ["files.HttpTikaResource"]
        }
    }


class TestDocument(HarvestDocument):

    tasks = models.JSONField(default=default_document_tasks, blank=True)
    is_not_found = models.BooleanField(default=False)
    status_code = models.SmallIntegerField(default=-1)
    redirects = models.CharField(max_length=50, choices=Redirects.choices, default=Redirects.NO)

    property_defaults = SEED_DEFAULTS

    def apply_resource(self, resource: Resource):
        if isinstance(resource, CheckURLResource):
            if resource.status == 404:
                self.is_not_found = True
                self.pending_at = None
                self.finished_at = now()

    def get_language(self):
        return self.properties.get("language", None)


class Overwrite(HarvestOverwrite):

    class Meta:
        verbose_name = "test overwrite"
        verbose_name_plural = "test overwrites"
