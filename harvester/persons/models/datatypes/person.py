from django.db import models

from core.models.datatypes import HarvestDocument
from search.clients import prepare_suggest_completion
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

    def to_data(self, merge_derivatives: bool = True, for_search: bool = True,
                use_multilingual_fields: bool = True) -> dict:
        data = super().to_data(merge_derivatives=merge_derivatives, use_multilingual_fields=use_multilingual_fields)
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

    def to_search(self, use_multilingual_fields: bool = False) -> dict:
        data = super().to_search(use_multilingual_fields=True)
        if self.state != self.States.ACTIVE:
            return data

        name = data["name"]
        description = data["description"]
        if description:
            suggest_completion = description.split(" ")[:1000]
            suggest_completion = [name] + prepare_suggest_completion(*suggest_completion)
        else:
            suggest_completion = [name] if name else []
        data["suggest_phrase"] = description
        data["suggest_completion"] = suggest_completion
        return data
