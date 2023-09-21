from django.db import models

from core.models.datatypes import HarvestDataset, HarvestDatasetVersion, HarvestSet


class Set(HarvestSet):

    class Meta:
        verbose_name = "product set"
        verbose_name_plural = "product set"


class Dataset(HarvestDataset):

    entities = models.ManyToManyField("sources.HarvestEntity", through="HarvestState", related_name="+")

    class Meta:
        verbose_name = "product dataset"
        verbose_name_plural = "product datasets"


class DatasetVersion(HarvestDatasetVersion):

    class Meta:
        verbose_name = "product dataset version"
        verbose_name_plural = "product dataset version"
