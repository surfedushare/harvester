from django.db import models

from core.models.datatypes import HarvestDataset, HarvestDatasetVersion, HarvestSet


class Set(HarvestSet):

    class Meta:
        verbose_name = "testing set"
        verbose_name_plural = "testing set"


class Dataset(HarvestDataset):

    entities = models.ManyToManyField("sources.HarvestEntity", through="HarvestState", related_name="+")

    class Meta:
        verbose_name = "testing dataset"
        verbose_name_plural = "testing datasets"


def default_dataset_version_tasks():
    return {
        "testing_after_dataset_version": {
            "depends_on": [],
            "checks": [],
            "resources": []
        }
    }


class DatasetVersion(HarvestDatasetVersion):

    tasks = models.JSONField(default=default_dataset_version_tasks, blank=True)

    class Meta:
        verbose_name = "testing dataset version"
        verbose_name_plural = "testing dataset version"
