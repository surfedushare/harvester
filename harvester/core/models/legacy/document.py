import re
from copy import copy
from unidecode import unidecode
from django.db import models

from datagrowth.datatypes import DocumentBase
from metadata.models import MetadataValue


PRIVATE_PROPERTIES = ["from_youtube", "lowest_educational_level"]


class DocumentManager(models.Manager):

    def build_from_seed(self, seed, collection=None, metadata_pipeline_key=None):
        properties = copy(seed)
        metadata_pipeline = properties.pop(metadata_pipeline_key, None)
        document = Document(properties=properties, collection=collection, pipeline={"metadata": metadata_pipeline})
        if collection:
            document.dataset_version = collection.dataset_version
        document.clean()
        return document


class Document(DocumentBase):

    class States(models.TextChoices):
        ACTIVE = "active", "Active"
        DELETED = "deleted", "Deleted"
        INACTIVE = "inactive", "In-active"

    objects = DocumentManager()

    dataset_version = models.ForeignKey("DatasetVersion", blank=True, null=True, on_delete=models.CASCADE)
    pipeline = models.JSONField(default=dict, blank=True)
    extension = models.ForeignKey("core.Extension", null=True, blank=True, on_delete=models.SET_NULL)
    # NB: Collection foreign key is added by the base class

    def apply_resource(self, resource):
        pass

    def update(self, data, commit=True, validate=True):
        if "language" in self.properties:
            data.pop("language", None)
        super().update(data, commit=commit, validate=validate)

    def get_language(self):
        language = self.properties.get('language', None)
        if language is None:
            return
        return language.get("metadata", "unk")

    def get_search_document_extras(self, reference_id, title, text, video, material_types,
                                   learning_material_disciplines):
        suggest_completion = []
        if title:
            suggest_completion += title.split(" ")
        if text:
            suggest_completion += text.split(" ")[:1000]
        alpha_pattern = re.compile("[^a-zA-Z]+")
        suggest_completion = [  # removes reading signs and acutes for autocomplete suggestions
            alpha_pattern.sub("", unidecode(word))
            for word in suggest_completion
        ]
        learning_material_disciplines_normalized = set([
            metadata_value.get_root().value if metadata_value.get_root() else metadata_value.value
            for metadata_value in MetadataValue.objects.filter(value__in=learning_material_disciplines,
                                                               field__name="learning_material_disciplines")
        ])
        extras = {
            '_id': reference_id,
            "language": self.get_language(),
            'suggest_completion': suggest_completion,
            'harvest_source': self.collection.name,
            'text': text,
            'suggest_phrase': text,
            'video': video,
            'material_types': material_types,
            'learning_material_disciplines_normalized': list(learning_material_disciplines_normalized),
            'learning_material_themes_normalized': list(learning_material_disciplines_normalized)
        }
        return extras

    def get_extension_extras(self, merge_extension):
        extension_data = copy(self.extension.properties) if merge_extension else {}
        extension_data["extension"] = {
            "id": self.extension.id,
            "is_addition": self.extension.is_addition
        }
        if self.extension.is_addition and merge_extension:
            extension_data["provider"] = {
                "ror": None,
                "external_id": None,
                "name": "Publinova",
                "slug": None
            }
        return extension_data

    def to_data(self):
        data = copy(self.properties)
        data["extension"] = None
        return data

    def to_search(self):
        # Get the basic document information including from document extensions
        search_base = self.to_data()
        # Decide whether to delete or not from the index
        if search_base["state"] != "active":
            yield {
                "_id": self.properties["external_id"],
                "_op_type": "delete"
            }
            return
        # Transform the data to the structure we actually want for search engine
        search_base.pop("language", None)
        text = search_base.pop("text", None)
        if text and len(text) >= 1000000:
            text = " ".join(text.split(" ")[:10000])
        for private_property in PRIVATE_PROPERTIES:
            search_base.pop(private_property, False)
        video = search_base.pop("video", None)
        material_types = search_base.pop("material_types", None) or ["unknown"]
        search_base["disciplines"] = search_base.get("studies", [])
        search_details = self.get_search_document_extras(
            self.properties["external_id"],
            self.properties["title"],
            text,
            video,
            material_types=material_types,
            learning_material_disciplines=search_base.get("learning_material_disciplines", [])
        )
        search_details.update(search_base)
        yield search_details
