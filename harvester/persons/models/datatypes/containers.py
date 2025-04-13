from django.db import models

from core.models.datatypes import HarvestDataset, HarvestDatasetVersion, HarvestSet


class Set(HarvestSet):

    class Meta:
        verbose_name = "person set"
        verbose_name_plural = "person set"


class Dataset(HarvestDataset):

    entities = models.ManyToManyField("sources.HarvestEntity", through="HarvestState", related_name="+")

    class Meta:
        verbose_name = "person dataset"
        verbose_name_plural = "person datasets"


class DatasetVersion(HarvestDatasetVersion):

    class Meta:
        verbose_name = "person dataset version"
        verbose_name_plural = "person dataset version"
