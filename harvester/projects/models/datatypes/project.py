from django.db import models

from core.models.datatypes import HarvestDocument

from projects.constants import SEED_DEFAULTS


def default_document_tasks():
    return {}


class ProjectDocument(HarvestDocument):

    tasks = models.JSONField(default=default_document_tasks, blank=True)
    overwrite = None

    property_defaults = SEED_DEFAULTS
