from django.db import models

from core.models.datatypes import HarvestDocument

from persons.constants import SEED_DEFAULTS


def default_document_tasks():
    return {
        "deactivate_invalid_documents": {
            "depends_on": [],
            "checks": [],
            "resources": []
        }
    }


class PersonDocument(HarvestDocument):

    tasks = models.JSONField(default=default_document_tasks, blank=True)
    overwrite = None

    property_defaults = SEED_DEFAULTS

    def to_data(self, merge_derivatives: bool = True, use_multilingual_fields: bool = True) -> dict:
        data = super().to_data(merge_derivatives, use_multilingual_fields)
        researcher = data.pop("researcher", {})
        if researcher:
            data.update(researcher)
        author = data.pop("author", {})
        if author:
            data.update(author)
        sensitive = data.pop("sensitive", {})
        if sensitive:
            data.update(sensitive)
        return data
