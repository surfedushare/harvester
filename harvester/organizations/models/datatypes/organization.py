from django.db import models

from core.models.datatypes import HarvestDocument
from search.clients import prepare_suggest_completion
from organizations.constants import SEED_DEFAULTS


def default_document_tasks():
    return {
        "deactivate_invalid_documents": {
            "depends_on": [],
            "checks": [],
            "resources": []
        }
    }


class OrganizationDocument(HarvestDocument):

    tasks = models.JSONField(default=default_document_tasks, blank=True)
    overwrite = None

    property_defaults = SEED_DEFAULTS

    def to_data(self, merge_derivatives: bool = True, for_search: bool = True,
                use_multilingual_fields: bool = False) -> dict:
        data = super().to_data(merge_derivatives, for_search, use_multilingual_fields)
        # The provider for Organization is a difficult case, because a provider is always an organization.
        # Therefor it's somewhat of a circular reference, which we need to break somehow.
        # The rules for determining the organization provider are as follows:
        #    1)   The secretary name if a secretary is set
        #    2)   The organization root if organization document is part of a hierarchy
        #    3)   Whatever default the HarvestDocument parent class decides on
        # Missing names for secretary or parent objects result in using the HarvestDocument default.
        # The system can't make a decision earlier, because complete parent data is only available after task execution.
        provider_default = data["provider"]
        if secretary := data.get("secretary"):
            data["provider"] = secretary.get("name", provider_default)
        elif parents := data.get("parents", []):
            for parent in parents:
                if parent.get("is_root", False):
                    data["provider"] = parent.get("name", provider_default)
                    break
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
