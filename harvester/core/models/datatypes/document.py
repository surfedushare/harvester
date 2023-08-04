from typing import Any
from copy import copy
from sentry_sdk import capture_message

from django.db import models
from django.utils.timezone import now

from datagrowth.datatypes import DocumentBase


def document_metadata_default() -> dict:
    return {
        "srn": None,
        "provider": {
            "name": None,
            "external_id": None,
            "slug": None,
            "ror": None
        },
        "created_at": None,
        "modified_at": None,
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


class HarvestDocument(DocumentBase):

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
    metadata = models.JSONField(default=document_metadata_default, blank=True)
    pipeline = models.JSONField(default=dict, blank=True)
    conditions = models.JSONField(default=dict, blank=True)
    derivatives = models.JSONField(default=dict, blank=True)
    pending_at = models.DateTimeField(default=now)

    def update(self, data: Any, commit: bool = True, validate: bool = True) -> None:
        super().update(data, commit=commit, validate=validate)

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
