from typing import Any
from copy import copy
import json
from hashlib import sha1
from sentry_sdk import capture_message

from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.timezone import now

from datagrowth.datatypes import DocumentBase
from core.models.datatypes.base import HarvestObjectMixin
from core.utils.decoders import HarvesterJSONDecoder


def document_metadata_default() -> dict:
    now_datetime = now()
    return {
        "srn": None,
        "provider": {
            "name": None,
            "external_id": None,
            "slug": None,
            "ror": None
        },
        "hash": None,
        "created_at": now_datetime,
        "modified_at": now_datetime,
        "deleted_at": None
    }


class HarvestDocumentManager(models.Manager):

    def build_from_seed(self, seed, collection=None, metadata_pipeline_key=None):
        properties = copy(seed)
        metadata_pipeline = properties.pop(metadata_pipeline_key, None)
        document = HarvestDocument(
            properties=properties,
            collection=collection,
            pipeline={"metadata": metadata_pipeline}
        )
        if collection:
            document.dataset_version = collection.dataset_version
        document.clean()
        return document

    def batches_from_seeds(self, seeds):
        pass

    def get_from_seed(self, seed):
        pass


class HarvestDocument(DocumentBase, HarvestObjectMixin):

    # NB: These foreign keys are app agnostic and point to different models in different apps
    dataset_version = models.ForeignKey("DatasetVersion", blank=True, null=True, on_delete=models.CASCADE)
    collection = models.ForeignKey("Set", blank=True, null=True,
                                   on_delete=models.CASCADE, related_name="document_set")
    overwrite = models.ForeignKey("Overwrite", null=True, blank=True, on_delete=models.SET_NULL)

    class States(models.TextChoices):
        ACTIVE = "active", "Active"
        DELETED = "deleted", "Deleted"
        INACTIVE = "inactive", "In-active"
        SKIPPED = "skipped", "Skipped"

    objects = HarvestDocumentManager()

    state = models.CharField(max_length=50, choices=States.choices, default=States.ACTIVE)
    metadata = models.JSONField(
        default=document_metadata_default, blank=True,
        encoder=DjangoJSONEncoder, decoder=HarvesterJSONDecoder
    )

    @classmethod
    def build(cls, data, collection=None):
        instance = super().build(data, collection)
        instance.dataset_version = collection.dataset_version
        instance.clean()
        return instance

    def update(self, data: Any, commit: bool = True) -> None:
        content = data.properties if isinstance(data, DocumentBase) else data
        for key, value in content.items():
            pass
        # Updates properties unless state is deleted
        if content.get("state") == self.States.DELETED.value:
            super().update({"state": self.States.DELETED.value}, commit=commit)
            self.metadata["deleted_at"] = now()
        else:
            super().update(data, commit=commit)
            self.metadata["deleted_at"] = None
        # Calculates the new properties hash and sets fields accordingly
        properties_string = json.dumps(self.properties, sort_keys=True, default=str)
        properties_hash = sha1(properties_string.encode("utf-8")).hexdigest()
        if properties_hash != self.metadata["hash"]:
            self.pending_at = now()
            self.metadata["hash"] = properties_hash
            self.metadata["modified_at"] = now()

    def apply_resource(self, resource):
        pass

    def get_derivatives_data(self) -> dict:
        data = {}
        for base, derivatives in self.derivatives.items():
            for key, value in derivatives.items():
                if key in data:
                    warning = f"Derivative based on '{base}' is trying to add '{key}', but this has already been set."
                    capture_message(warning, level="warning")
                    continue
                data[key] = value
        return data

    def to_data(self, merge_derivatives: bool = True) -> dict:
        data = copy(self.properties)
        if self.overwrite:
            data["overwrite"] = self.overwrite.id
            data.update(self.overwrite)
        else:
            data["overwrite"] = None
        if merge_derivatives:
            data.update(self.get_derivatives_data())
        return data

    def to_search(self) -> list[dict]:
        # Get the basic document information including from document overwrites
        search_data = self.to_data()
        # Decide whether to delete or not from the index
        if self.state != "active":
            yield {
                "_id": self.properties["external_id"],
                "_op_type": "delete"
            }
            return
        yield search_data

    class Meta:
        abstract = True
