from django.db import models

from core.models.datatypes import HarvestDataset, HarvestDatasetVersion, HarvestSet


class Set(HarvestSet):

    class Meta:
        verbose_name = "project set"
        verbose_name_plural = "project set"


class Dataset(HarvestDataset):

    entities = models.ManyToManyField("sources.HarvestEntity", through="HarvestState", related_name="+")

    class Meta:
        verbose_name = "project dataset"
        verbose_name_plural = "project datasets"


class DatasetVersion(HarvestDatasetVersion):

    class Meta:
        verbose_name = "project dataset version"
        verbose_name_plural = "project dataset version"
