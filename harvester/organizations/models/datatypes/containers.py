from django.db import models

from core.models.datatypes import HarvestDataset, HarvestDatasetVersion, HarvestSet


def default_set_tasks():
    return {
        "check_set_integrity": {
            "depends_on": [],
            "checks": [],
            "resources": []
        },
        "lookup_organization_parents": {
            "depends_on": [],
            "checks": [],
            "resources": []
        }
    }


class Set(HarvestSet):

    tasks = models.JSONField(default=default_set_tasks, blank=True)

    class Meta:
        verbose_name = "organization set"
        verbose_name_plural = "organization set"


class Dataset(HarvestDataset):

    entities = models.ManyToManyField("sources.HarvestEntity", through="HarvestState", related_name="+")

    class Meta:
        verbose_name = "organization dataset"
        verbose_name_plural = "organization datasets"


class DatasetVersion(HarvestDatasetVersion):

    class Meta:
        verbose_name = "organization dataset version"
        verbose_name_plural = "organization dataset version"
