from typing import Any
from copy import copy, deepcopy
import json
from hashlib import sha1
from sentry_sdk import capture_message

from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.timezone import now

from datagrowth.utils import reach
from datagrowth.datatypes import DocumentBase
from core.models.datatypes.base import HarvestObjectMixin
from core.utils.decoders import HarvesterJSONDecoder


def document_metadata_default() -> dict:
    current_time = now()
    return {
        "srn": None,
        "provider": {
            "name": None,
            "external_id": None,
            "slug": None,
            "ror": None
        },
        "hash": None,
        "created_at": current_time,
        "modified_at": current_time,
        "deleted_at": None
    }


class HarvestDocument(DocumentBase, HarvestObjectMixin):

    # NB: These foreign keys are app agnostic and point to different models in different apps
    dataset_version = models.ForeignKey("DatasetVersion", blank=True, null=True, on_delete=models.CASCADE,
                                        related_name="documents")
    collection = models.ForeignKey("Set", blank=True, null=True,
                                   on_delete=models.CASCADE, related_name="document_set")
    overwrite = models.ForeignKey("Overwrite", null=True, blank=True, on_delete=models.SET_NULL)

    class States(models.TextChoices):
        ACTIVE = "active", "Active"
        DELETED = "deleted", "Deleted"
        INACTIVE = "inactive", "In-active"
        SKIPPED = "skipped", "Skipped"

    state = models.CharField(max_length=50, choices=States.choices, default=States.ACTIVE, db_index=True)
    metadata = models.JSONField(
        default=document_metadata_default, blank=True,
        encoder=DjangoJSONEncoder, decoder=HarvesterJSONDecoder
    )

    property_defaults = {}

    @classmethod
    def build(cls, data, collection=None):
        data = cls.parse_seed_data(data)
        data["srn"] = f"{data['set']}:{data['external_id']}"
        instance = super().build(data, collection)
        instance.dataset_version = collection.dataset_version
        instance.clean()
        return instance

    @staticmethod
    def parse_seed_data(data: dict) -> dict:
        output = {}
        for key, value in data.items():
            if "." in key:
                parent_key, child_key = key.split(".")
                if parent_key not in output:
                    output[parent_key] = {}
                output[parent_key][child_key] = value
            else:
                output[key] = value
        return output

    def update(self, data: Any, commit: bool = True) -> None:
        current_time = now()
        content = data.properties if isinstance(data, DocumentBase) else data
        # See if pipeline task need to re-run due to changes
        for dependency_key, task_names in self.get_property_dependencies().items():
            current_value = reach(dependency_key, self.properties)
            update_value = reach(dependency_key, content)
            if current_value != update_value:
                for task in task_names:
                    self.invalidate_task(task, current_time=current_time)
        # Updates properties unless state is deleted
        if content.get("state") == self.States.DELETED.value:
            super().update({"state": self.States.DELETED.value}, commit=commit)
        else:
            data = self.parse_seed_data(data)
            super().update(data, commit=commit)

    def clean(self):
        super().clean()
        current_time = now()
        # Update metadata about deletion
        self.state = self.properties.get("state", None)
        if self.state == self.States.DELETED.value and not self.metadata.get("deleted_at", None):
            self.metadata["deleted_at"] = current_time
            self.metadata["modified_at"] = current_time
        elif self.state != self.States.DELETED.value:
            self.metadata["deleted_at"] = None
        # Sets defaults for properties
        for key, value in self.property_defaults.items():
            if key not in self.properties:
                self.properties[key] = value
        # Calculates the properties hash and (re)sets it.
        # The modified_at metadata only changes when the hash changes, not when we first create the hash.
        properties_string = json.dumps(self.properties, sort_keys=True, default=str)
        properties_hash = sha1(properties_string.encode("utf-8")).hexdigest()
        if self.metadata.get("hash", None) is None:
            self.metadata["hash"] = properties_hash
        elif properties_hash != self.metadata["hash"]:
            self.metadata["hash"] = properties_hash
            self.metadata["modified_at"] = current_time

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
        # Decide whether to delete or not from the index
        if self.state != "active":
            yield {
                "_id": self.properties["srn"],
                "_op_type": "delete"
            }
            return
        # Get the basic document information including from document overwrites
        search_data = self.to_data()
        search_data["_id"] = self.properties["srn"]
        yield search_data

    def __eq__(self, other):
        if not isinstance(other, HarvestDocument):
            return NotImplemented()
        content_hash = self.metadata.get("hash", None)
        deleted_at = self.metadata.get("deleted_at", None)
        return content_hash and content_hash == other.metadata.get("hash", None) and \
            deleted_at == other.metadata.get("deleted_at", None)

    def __hash__(self):
        content_hash = self.metadata.get("hash", None)
        return int(content_hash, 16) if content_hash else super().__hash__()

    class Meta:
        abstract = True
