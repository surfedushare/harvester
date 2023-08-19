from django.db import models

from core.models.datatypes import HarvestDataset, HarvestDatasetVersion, HarvestSet


class Set(HarvestSet):

    class Meta:
        verbose_name = "file overwrite"
        verbose_name_plural = "file overwrites"


class Dataset(HarvestDataset):

    entities = models.ManyToManyField("sources.HarvestEntity", through="HarvestState")

    class Meta:
        verbose_name = "file dataset"
        verbose_name_plural = "file datasets"


class DatasetVersion(HarvestDatasetVersion):

    class Meta:
        verbose_name = "file dataset version"
        verbose_name_plural = "file dataset version"
