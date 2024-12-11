from django.db import models

from core.models.datatypes import HarvestDataset, HarvestDatasetVersion, HarvestSet


class Set(HarvestSet):

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
