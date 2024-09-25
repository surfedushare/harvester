from django.db import models

from core.models.datatypes import HarvestDocument

from projects.constants import SEED_DEFAULTS


def default_document_tasks():
    return {}


class ProjectDocument(HarvestDocument):

    tasks = models.JSONField(default=default_document_tasks, blank=True)
    overwrite = None

    property_defaults = SEED_DEFAULTS

    def to_data(self, merge_derivatives: bool = True, use_multilingual_fields: bool = False) -> dict:
        data = super().to_data(merge_derivatives, use_multilingual_fields)
        research_product = data.pop("research_project", {})
        if research_product:
            data.update(research_product)
