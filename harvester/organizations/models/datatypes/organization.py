from django.db import models

from core.models.datatypes import HarvestDocument

from organizations.constants import SEED_DEFAULTS


def default_document_tasks():
    return {
        "deactivate_invalid_organizations": {
            "depends_on": ["$.modified_at"],
            "checks": [],
            "resources": []
        }
    }


class OrganizationDocument(HarvestDocument):

    tasks = models.JSONField(default=default_document_tasks, blank=True)
    overwrite = None

    property_defaults = SEED_DEFAULTS
