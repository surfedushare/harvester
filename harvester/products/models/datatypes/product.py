import re
from unidecode import unidecode
from hashlib import sha1

from django.db import models
from django.conf import settings

from core.models.datatypes import HarvestDocument, HarvestOverwrite
from metadata.models import MetadataValue
from files.models import FileDocument


def default_document_tasks():
    tasks = {}
    if settings.PROJECT == "edusources":
        tasks["lookup_study_vocabulary_parents"] = {
            "depends_on": ["$.learning_material.study_vocabulary"],
            "checks": ["has_study_vocabulary"],
            "resources": []
        }
        tasks["normalize_disciplines"] = {
            "depends_on": ["$.learning_material.disciplines"],
            "checks": ["has_disciplines"],
            "resources": []
        }
    return tasks


class ProductDocument(HarvestDocument):

    tasks = models.JSONField(default=default_document_tasks, blank=True)

    @property
    def has_study_vocabulary(self) -> bool:
        study_vocabulary_ids = self.properties.get("learning_material", {}).get("study_vocabulary", [])
        if not study_vocabulary_ids:
            return False
        return MetadataValue.objects.filter(field__name="study_vocabulary", value__in=study_vocabulary_ids).exists()

    @property
    def has_disciplines(self) -> bool:
        discipline_ids = self.properties.get("learning_material", {}).get("disciplines", [])
        if not discipline_ids:
            return False
        return MetadataValue.objects \
            .filter(field__name="learning_material_disciplines_normalized", value__in=discipline_ids) \
            .exists()

    def get_language(self) -> str:
        return self.metadata["language"]

    @staticmethod
    def update_files_data(data: dict) -> dict:
        # Prepare lookups
        file_identities = [
            f"{data['set']}:{sha1(url.encode('utf-8')).hexdigest()}"
            for url in data["files"]
        ]
        files_by_identity = {
            file_document.identity: file_document.to_data()
            for file_document in FileDocument.objects.filter(identity__in=file_identities, is_not_found=False)
        }
        # Get the first file and merge its info into the product
        # If the product sets a technical_type we ignore the file technical_type
        first_file_document = next(
            (files_by_identity[identity] for identity in file_identities if identity in files_by_identity),
            None
        )
        if first_file_document:
            main_file_info = {
                "url": first_file_document["url"],
                "mime_type": first_file_document["mime_type"],
                "technical_type": first_file_document["type"],
                "text": first_file_document.get("text", None),
                "previews": first_file_document.get("previews", None),
                "video": first_file_document.get("video", None),
            }
            if data.get("technical_type", None):
                main_file_info.pop("technical_type")
            data.update(main_file_info)
        # Clean the file data a bit and set titles for links
        links_in_order = [
            file_identity for file_identity in file_identities
            if file_identity in files_by_identity and files_by_identity[file_identity]["is_link"]
        ]
        files = []
        for file_identity in file_identities:
            file_info = files_by_identity.get(file_identity, None)
            if not file_info:
                continue
            if "text" in file_info:
                del file_info["text"]
            if file_info["is_link"] and not file_info["title"]:
                links_index = links_in_order.index(file_identity)
                file_info["title"] = f"URL {links_index+1}"
            files.append(file_info)
        # Return the product with updated files data
        data["files"] = files
        return data

    @staticmethod
    def get_suggest_completion(title: str, text: str) -> list[str]:
        suggest_completion = []
        if title:
            suggest_completion += title.split(" ")
        if text:
            suggest_completion += text.split(" ")[:1000]
        alpha_pattern = re.compile("[^a-zA-Z]+")
        return [  # removes reading signs and acutes for autocomplete suggestions
            alpha_pattern.sub("", unidecode(word))
            for word in suggest_completion
        ]

    def transform_search_data(self, data: dict) -> dict:
        text = data.pop("text", None)
        if text and len(text) >= 1000000:
            text = " ".join(text.split(" ")[:10000])
        data["text"] = text
        data["suggest_phrase"] = text
        data["suggest_completion"] = self.get_suggest_completion(data["title"], text)
        return data

    def get_derivatives_data(self) -> dict:
        data = super().get_derivatives_data()
        if "learning_material_disciplines_normalized" not in data:
            data["learning_material_disciplines_normalized"] = []
        return data

    def to_data(self, merge_derivatives: bool = True, for_search: bool = True) -> dict:
        data = super().to_data(merge_derivatives)
        source, set_name = data["set"].split(":")
        data["harvest_source"] = set_name
        if len(data["files"]):
            data = self.update_files_data(data)
        learning_material = data.pop("learning_material", None)
        if learning_material:
            learning_material["learning_material_disciplines"] = learning_material["disciplines"]
            learning_material["material_types"] = learning_material["material_types"] or ["unknown"]
            learning_material.pop("study_vocabulary", None)  # prevents overwriting derivatives data
            data.update(learning_material)
        research_product = data.pop("research_product", None)
        if research_product:
            data.update(research_product)
        if for_search:
            data = self.transform_search_data(data)
        return data

    def clean(self) -> None:
        super().clean()
        language = self.metadata.get("language", None)
        if language is None:
            source_language = self.properties.get("language", None)
            language_codes = settings.OPENSEARCH_LANGUAGE_CODES
            self.metadata["language"] = source_language if source_language in language_codes else "unk"


class Overwrite(HarvestOverwrite):

    class Meta:
        verbose_name = "product overwrite"
        verbose_name_plural = "product overwrites"
