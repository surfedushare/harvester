from typing import Any
from copy import copy, deepcopy
import json
from hashlib import sha1
from sentry_sdk import capture_message
from operator import xor

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
    def build(cls, data, collection=None, build_time=None):
        # Parse seed data will try to parse keys to enable nested data structures
        data = cls.parse_seed_data(data)
        # Surf Resource Name (SRN) can't always be extracted easily (looking at you Sharekit products).
        # Instead we defer the SRN based data upon build of the Document.
        data["srn"] = f"{data['set']}:{data['external_id']}" if data["external_id"] is not None else None
        # Standard build stuff where we set the dataset version as well.
        instance = super().build(data, collection)
        instance.dataset_version = collection.dataset_version
        instance.clean(set_metadata=False)
        instance.set_metadata(current_time=build_time, new=bool(build_time))
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
        # Deletes shouldn't update anything but state information
        if content.get("state") == self.States.DELETED.value:
            super().update({"state": self.States.DELETED.value}, commit=commit)
            return
        # See if pipeline task need to re-run due to changes
        for dependency_key, task_names in self.get_property_dependencies().items():
            current_value = reach(dependency_key, self.properties)
            update_value = reach(dependency_key, content)
            if current_value != update_value:
                for task in task_names:
                    self.invalidate_task(task, current_time=current_time)
        # Update as normal, but parse special keys
        data = self.parse_seed_data(data)
        super().update(data, commit=commit)

    def set_metadata(self, current_time=None, new=False):
        current_time = current_time or now()
        # Update metadata about creation
        if new:
            self.metadata["created_at"] = current_time
        # Update metadata about deletion
        self.state = self.properties.get("state", None)
        if self.state != self.States.ACTIVE and (not self.metadata.get("deleted_at", None) or new):
            self.metadata["deleted_at"] = current_time
            self.metadata["modified_at"] = current_time
            self.finish_processing(current_time, commit=False)
        elif self.state == self.States.ACTIVE:
            self.metadata["deleted_at"] = None
        # Calculates the properties hash and (re)sets it.
        # The modified_at metadata only changes when the hash changes, not when we first create the hash.
        properties_string = json.dumps(self.properties, sort_keys=True, default=str)
        properties_hash = sha1(properties_string.encode("utf-8")).hexdigest()
        if self.metadata.get("hash", None) is None:
            self.metadata["hash"] = properties_hash
        elif properties_hash != self.metadata["hash"]:
            self.metadata["hash"] = properties_hash
            self.metadata["modified_at"] = current_time

    def clean(self, set_metadata=True):
        super().clean()
        # Sets defaults for properties
        for key, value in self.property_defaults.items():
            if key not in self.properties:
                self.properties[key] = deepcopy(value)
            elif isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    if nested_key not in self.properties[key]:
                        self.properties[key][nested_key] = copy(nested_value)
        # Sets metadata properties based on "now"
        if set_metadata:
            self.set_metadata()

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
        data = deepcopy(self.properties)
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
        if self.state != self.States.ACTIVE:
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
        # We won't try equality with anything but a HarvestDocument of the same class
        if not isinstance(other, type(self)):
            return NotImplemented
        # Harvester determines equality based on hash of data from sources inside properties field,
        # as well as whether that data should be considered deleted or not and
        # which dataset version the documents belong to.
        content_hash = self.metadata.get("hash", None)
        deleted_at = self.metadata.get("deleted_at", None)
        return content_hash and content_hash == other.metadata.get("hash", None) and \
            not xor(bool(deleted_at), bool(other.metadata.get("deleted_at", None))) and \
            self.dataset_version_id == other.dataset_version_id

    def __hash__(self):
        content_hash = self.metadata.get("hash", None)
        if not content_hash:
            return super().__hash__()
        hash_number = int(content_hash, 16)
        if self.dataset_version_id:
            hash_number += self.dataset_version_id
        return hash_number

    class Meta:
        abstract = True
