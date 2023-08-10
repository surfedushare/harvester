from __future__ import annotations

from collections import defaultdict
from itertools import groupby
from functools import reduce
from datetime import datetime

from django.conf import settings
from django.db import models, transaction
from django.db.models.manager import QuerySet

from datagrowth.utils import ibatch
from core.models.datatypes.base import HarvestObjectMixin
from core.models.datatypes.set import HarvestSet
from core.models.datatypes.document import HarvestDocument
from core.models.harvest import HarvestState


class HarvestDataset(models.Model):
    """
    The most overarching model for storing HarvestDocuments.
    It's assumed that any HarvestDocuments within a single Dataset have a similar schema.
    Meaning that any key in a HarvestDocument's properties will be present in
    any other HarvestDocument of the same Dataset.
    """
    name = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_latest = models.BooleanField(default=False)

    def __str__(self) -> str:
        return "{} (id={})".format(self.name, self.id)

    @classmethod
    def get_name(cls) -> str:  # adheres to Datagrowth protocol for easy data loads
        return f"{cls._meta.app_label}dataset"

    @property
    def harvests(self) -> HarvestState.objects | QuerySet:
        raise NotImplementedError(
            "The harvests property is not implemented by the concrete Dataset class. "
            "Add a ManyToMany field to HarvestSource through HarvestState on the Dataset "
            "and return the related manager from harvests property."
        )

    @transaction.atomic
    def create_new_version(self, excluded_specs: list[str] = None) -> HarvestDatasetVersion:
        excluded_specs = excluded_specs or []
        current_version = HarvestDatasetVersion.objects.get_current_version()
        new_version = self.versions.create(version=settings.VERSION, is_current=False)

        for harvest in self.harvests.all():
            if current_version and harvest.source.set_specification not in excluded_specs and \
                    not harvest.should_purge():
                collection = current_version.sets.filter(name=harvest.source.set_specification).last()
                if collection:
                    new_version.copy_collection(collection)

        return new_version

    def get_earliest_harvest_date(self) -> datetime:
        latest_harvest = self.harvests.order_by("harvested_at").first()
        return latest_harvest.harvested_at if latest_harvest else None

    def evaluate_dataset_version(self, new_version: HarvestDatasetVersion) -> list[HarvestSet]:
        current_version = self.versions.get_current_version()
        if not current_version or not new_version:
            return []
        fallback_collections = []
        current_aggregates = current_version.aggregate()
        new_aggregates = new_version.aggregate()
        for collection_name, collection_info in current_aggregates.items():
            document_count = collection_info["document_count"]
            if not document_count:
                continue
            if collection_name not in new_aggregates:
                fallback_collections.append(collection_info["collection"])
                continue
            new_count = new_aggregates[collection_name]["document_count"]
            count_diff = document_count - new_count
            if count_diff and count_diff / document_count >= 0.05 and document_count > 50:
                fallback_collections.append(collection_info["collection"])
        return fallback_collections

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


class HarvestDatasetVersion(HarvestObjectMixin):

    objects = HarvestDatasetVersionManager()

    dataset = models.ForeignKey("Dataset", on_delete=models.CASCADE, null=False, blank=False,
                                related_name="versions")
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    version = models.CharField(max_length=50, null=False, blank=True)

    @property
    def documents(self) -> HarvestDocument.objects | QuerySet:
        return self.document_set

    @property
    def sets(self) -> HarvestSet.objects | QuerySet:
        return self.collection_set

    def __str__(self):
        return "{} (v={}, id={})".format(self.dataset.name, self.version, self.id)

    def copy_set(self, source_set: HarvestSet) -> HarvestSet:
        Document = source_set.get_document_model()
        source_id = source_set.id
        source_set.pk = None
        source_set.id = None
        source_set.dataset_version = self
        source_set.save()
        for batch in ibatch(Document.objects.filter(collection_id=source_id), batch_size=100):
            for doc in batch:
                doc.collection_id = source_set.id
                doc.dataset_version = self
                doc.pk = None
                doc.id = None
            Document.objects.bulk_create(batch)
        return source_set

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
        HarvestDatasetVersion.objects.all().update(is_current=False)
        self.is_current = True
        self.save()

    def aggregate(self) -> dict[str, dict[str, HarvestSet | int]]:
        return {
            collection.name: {
                "collection": collection,
                "document_count": collection.document_set.filter(dataset_version=self).count()
            }
            for collection in self.sets.all()
        }

    class Meta:
        abstract = True
        get_latest_by = "-created_at"
