from __future__ import annotations

from collections import defaultdict
from itertools import groupby
from functools import reduce
from datetime import datetime

from django.conf import settings
from django.db import models

from core.models.datatypes.base import HarvestObjectMixin


class HarvestDataset(models.Model):
    """
    The most overarching model for storing HarvestDocuments.
    It's assumed that any HarvestDocuments within a single Dataset have a similar schema.
    Meaning that any key in a HarvestDocument's properties will be present in
    any other HarvestDocument of the same Dataset.
    """

    class IndexingOptions(models.TextChoices):
        NO = "no", "No"
        INDEX_ONLY = "index_only", "Index only"
        INDEX_AND_PROMOTE = "index_and_promote", "Index and promote"

    name = models.CharField(max_length=255, null=True, blank=True)
    is_harvested = models.BooleanField(default=False)
    indexing = models.CharField(max_length=50, choices=IndexingOptions.choices, default=IndexingOptions.NO)

    def __str__(self) -> str:
        return "{} (id={})".format(self.name, self.id)

    @classmethod
    def get_name(cls) -> str:  # adheres to Datagrowth protocol for easy data loads
        return f"{cls._meta.app_label}.dataset"

    class Meta:
        abstract = True


class HarvestDatasetVersionManager(models.Manager):

    def get_latest_version(self, dataset: HarvestDataset = None,
                           dataset_name: str = None) -> HarvestDatasetVersion | None:
        filters = {
            "version": settings.VERSION
        }
        if dataset:
            filters.update({"dataset": dataset})
        elif dataset_name:
            filters.update({"dataset__name": dataset_name})
        return super().get_queryset().filter(**filters).last()

    def get_current_version(self) -> HarvestDatasetVersion | None:
        return super().get_queryset().filter(is_current=True).last()

    @staticmethod
    def reduce_version_integer(dataset_version: HarvestDatasetVersion) -> int:
        def _reduce_version_integer(value, ix_element):
            ix, element = ix_element
            multiplier = pow(1000, ix)
            integer = multiplier * int(element) if multiplier else int(element)
            return value + integer
        version_split = dataset_version.version.split(".")
        version_split.reverse()
        result = reduce(_reduce_version_integer, enumerate(version_split), 0)
        return result

    def get_stale_versions(self, purge_time: datetime, dataset: HarvestDataset) -> list[int]:
        queryset = self.get_queryset().filter(dataset=dataset, is_current=False).order_by("version", "created_at")
        grouped_versions = {
            group: list(versions)
            for group, versions in groupby(queryset, self.reduce_version_integer)
        }
        version_keys = sorted(grouped_versions.keys(), reverse=True)
        retained_versions = []
        stale_versions = []
        for version_key in version_keys:
            dataset_versions = grouped_versions[version_key]
            if len(retained_versions) < settings.DATA_RETENTION_KEEP_VERSIONS:
                retained_versions.append(dataset_versions.pop())
                stale_versions += dataset_versions
            else:
                stale_versions += dataset_versions
        return [
            stale_version for stale_version in stale_versions
            if stale_version.created_at <= purge_time
        ]


def default_dataset_version_tasks():
    return {
        "set_current_dataset_version": {
            "depends_on": [],
            "checks": [],
            "resources": []
        },
        "create_opensearch_index": {
            "depends_on": ["set_current_dataset_version"],
            "checks": [],
            "resources": []
        },
    }


def version_default() -> str:
    return settings.VERSION


class HarvestDatasetVersion(HarvestObjectMixin):

    objects = HarvestDatasetVersionManager()

    dataset = models.ForeignKey("Dataset", on_delete=models.CASCADE, null=False, blank=False, related_name="versions")
    index = models.ForeignKey(
        "search.OpenSearchIndex",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+"
    )
    historic_sets = models.ManyToManyField(to="Set", blank=True)

    is_current = models.BooleanField(default=False)
    is_index_promoted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    version = models.CharField(max_length=50, null=False, blank=True, default=version_default)
    tasks = models.JSONField(default=default_dataset_version_tasks, blank=True)

    def __str__(self) -> str:
        return "{} (v={}, id={})".format(self.dataset.name, self.version, self.id)

    @property
    def natural_key(self) -> tuple[str, int]:
        return f"{self._meta.app_label}.{self._meta.model_name}", self.id,

    def get_search_documents_by_language(self, **filters) -> dict[str, list]:
        by_language = defaultdict(list)
        documents = self.documents.filter(**filters)
        for document in documents:
            language = document.get_language()
            if language not in settings.OPENSEARCH_ANALYSERS:
                language = "unk"
            by_language[language] += list(document.to_search())
        return by_language

    def set_current(self) -> None:
        type(self).objects.all().update(is_current=False)
        self.is_current = True
        self.save()

    def set_index_promoted(self) -> None:
        type(self).objects.all().update(is_index_promoted=False)
        self.is_index_promoted = True
        self.save()

    class Meta:
        abstract = True
        get_latest_by = "-created_at"
