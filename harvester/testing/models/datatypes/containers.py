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


class DatasetVersion(HarvestDatasetVersion):

    class Meta:
        verbose_name = "testing dataset version"
        verbose_name_plural = "testing dataset version"
