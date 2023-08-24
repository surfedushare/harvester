from __future__ import annotations

from django.apps import apps
from django.db import models

from datagrowth.datatypes import CollectionBase, DocumentCollectionMixin

from core.constants import DELETE_POLICY_CHOICES
from core.models.datatypes.base import HarvestObjectMixin
from core.models.datatypes.document import HarvestDocument


def default_set_tasks():
    return {
        "apply_set_deletes": {
            "depends_on": [],
            "checks": [],
            "resources": []
        },
        "check_set_integrity": {
            "depends_on": ["apply_set_deletes"],
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
    delete_policy = models.CharField(max_length=50, choices=DELETE_POLICY_CHOICES, null=True, blank=True)

    tasks = models.JSONField(default=default_set_tasks, blank=True)
    pending_at = models.DateTimeField(null=True, blank=True)  # sets are not pending until all source data is fetched

    @classmethod
    def get_document_model(cls) -> HarvestDocument:
        app_label = cls._meta.app_label
        app_config = apps.get_app_config(app_label)
        return apps.get_model(f"{app_label}.{app_config.document_model}")

    def init_document(self, data: dict, collection: HarvestSet = None) -> HarvestDocument:
        doc = super().init_document(data, collection=collection or self)
        doc.dataset_version = self.dataset_version
        return doc

    def __str__(self) -> str:
        return "{} (id={})".format(self.name, self.id)

    class Meta:
        abstract = True
