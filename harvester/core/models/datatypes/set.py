from __future__ import annotations

from django.apps import apps
from django.db import models

from datagrowth.datatypes import CollectionBase, DocumentCollectionMixin
from datagrowth.utils import ibatch

from core.constants import DELETE_POLICY_CHOICES
from core.models.datatypes.base import HarvestObjectMixin
from core.models.datatypes.document import HarvestDocument


def default_set_tasks():
    return {
        "check_set_integrity": {
            "depends_on": [],
            "checks": [],
            "resources": []
        },
    }


class HarvestSet(DocumentCollectionMixin, CollectionBase, HarvestObjectMixin):
    """
    Represents a set as used by the OAI-PMH protocol.
    These sets are logically collections of documents.
    """

    dataset_version = models.ForeignKey(
        "DatasetVersion",
        blank=True, null=True,
        on_delete=models.CASCADE,
        related_name="sets"
    )

    name = models.CharField(max_length=255, null=True, blank=True)
    delete_policy = models.CharField(max_length=50, choices=DELETE_POLICY_CHOICES, null=True, blank=True)
    tasks = models.JSONField(default=default_set_tasks, blank=True)
    pending_at = models.DateTimeField(null=True, blank=True)  # sets are not pending until all source data is fetched

    @classmethod
    def get_document_model(cls) -> HarvestDocument:
        app_label = cls._meta.app_label
        app_config = apps.get_app_config(app_label)
        return apps.get_model(f"{app_label}.{app_config.document_model}")

    def build_document(self, data, collection=None):
        doc = super().build_document(data, collection=collection or self)
        doc.dataset_version = self.dataset_version
        return doc

    @property
    def document_update_fields(self) -> list[str]:
        fields = super().document_update_fields
        fields += ["state", "pipeline", "derivatives", "pending_at", "finished_at", "metadata"]
        return fields

    def copy_documents(self, source_set: HarvestSet):
        Document = self.get_document_model()
        for batch in ibatch(Document.objects.filter(collection_id=source_set.id), batch_size=100):
            for doc in batch:
                doc.collection_id = self.id
                doc.dataset_version = self.dataset_version
                doc.pk = None
                doc.id = None
            Document.objects.bulk_create(batch)

    def __str__(self) -> str:
        return "{} (id={})".format(self.name, self.id)

    class Meta:
        abstract = True
