from __future__ import annotations

from django.apps import apps
from django.db import models

from datagrowth.datatypes import CollectionBase, DocumentCollectionMixin

from core.models.datatypes.base import HarvestObjectMixin
from core.models.datatypes.document import HarvestDocument


class HarvestSet(DocumentCollectionMixin, CollectionBase, HarvestObjectMixin):
    """
    Represents a set as used by the OAI-PMH protocol.
    These sets are logically collections of documents.
    """

    dataset_version = models.ForeignKey("DatasetVersion", blank=True, null=True, on_delete=models.CASCADE)

    metadata = models.JSONField(default=simple_metadata_default, blank=True)
    pipeline = models.JSONField(default=dict, blank=True)
    conditions = models.JSONField(default=dict, blank=True)
    derivatives = models.JSONField(default=dict, blank=True)

    @classmethod
    def get_document_model(cls) -> HarvestDocument:
        app = cls._meta.app_label
        app_config = apps.get_app_config(app)
        return apps.get_model(app_config.document_model)

    def init_document(self, data: dict, collection: HarvestSet = None) -> HarvestDocument:
        doc = super().init_document(data, collection=collection or self)
        doc.dataset_version = self.dataset_version
        return doc

    def __str__(self) -> str:
        return "{} (id={})".format(self.name, self.id)

    class Meta:
        abstract = True
