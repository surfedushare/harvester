import re
from unidecode import unidecode
from hashlib import sha1

from django.db import models
from django.conf import settings

from core.models.datatypes import HarvestDocument, HarvestOverwrite
from core.utils.analyzers import get_analyzer_language
from core.utils.contents import ContentContainer, Content
from metadata.models import MetadataValue
from products.constants import SEED_DEFAULTS
from files.models import FileDocument


def default_document_tasks():
    tasks = {
        "normalize_publisher_year": {
            "depends_on": ["$.publisher_year"],
            "checks": ["has_publisher_year"],
            "resources": []
        },
        "deactivate_invalid_products": {
            "depends_on": ["$.modified_at"],
            "checks": [],
            "resources": []
        }
    }
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
        tasks["lookup_consortium_translations"] = {
            "depends_on": ["$.learning_material.consortium"],
            "checks": ["has_consortium"],
            "resources": []
        }
    return tasks


class ProductDocument(HarvestDocument):

    tasks = models.JSONField(default=default_document_tasks, blank=True)

    property_defaults = SEED_DEFAULTS

    @property
    def has_study_vocabulary(self) -> bool:
        study_vocabulary_ids = self.properties.get("learning_material", {}).get("study_vocabulary", [])
        if not study_vocabulary_ids:
            return False
        return MetadataValue.objects.filter(field__name="study_vocabulary.keyword", value__in=study_vocabulary_ids) \
            .exists()

    @property
    def has_disciplines(self) -> bool:
        discipline_ids = self.properties.get("learning_material", {}).get("disciplines", [])
        if not discipline_ids:
            return False
        return MetadataValue.objects \
            .filter(field__name="disciplines_normalized.keyword", value__in=discipline_ids) \
            .exists()

    @property
    def has_consortium(self) -> bool:
        return self.properties.get("learning_material", {}).get("consortium")

    @property
    def has_publisher_year(self) -> bool:
        publisher_year = self.properties.get("publisher_year")
        if not publisher_year:
            return False
        return MetadataValue.objects.filter(field__name="publisher_year", value=publisher_year).exists()

    def get_analyzer_language(self) -> str:
        return self.metadata["language"]

    @staticmethod
    def update_files_data(data: dict, content_container: ContentContainer) -> dict:
        # Prepare lookups
        file_identities = [
            f"{data['set']}:{data['external_id']}:{sha1(url.encode('utf-8')).hexdigest()}"
            for url in data["files"]
        ]
        files_by_identity = {
            file_document.identity: file_document.to_data()
            for file_document in FileDocument.objects.filter(identity__in=file_identities, is_not_found=False,
                                                             dataset_version__is_current=True)
        }
        prioritized_file_identities = sorted(
            file_identities,
            key=lambda file_id: files_by_identity.get(file_id, {}).get("priority", 0),
            reverse=True
        )
        # Get the first file and merge its info into the product
        # If the product sets a technical_type we ignore the file technical_type
        first_file_document = next(
            (files_by_identity[identity] for identity in prioritized_file_identities if identity in files_by_identity),
            {}
        )
        main_file_info = {
            "url": first_file_document.get("url"),
            "mime_type": first_file_document.get("mime_type"),
            "technical_type": first_file_document.get("type"),
            "previews": first_file_document.get("previews"),
            "video": first_file_document.get("video"),
            "copyright": first_file_document.get("copyright") or "yes"
        }
        if data.get("technical_type"):
            main_file_info.pop("technical_type")
        if data.get("copyright") or not settings.SET_PRODUCT_COPYRIGHT_BY_MAIN_FILE_COPYRIGHT:
            main_file_info.pop("copyright")
        data.update(main_file_info)
        # Clean the file data a bit and set titles for files
        files_in_order = []
        links_in_order = []
        for file_identity in prioritized_file_identities:
            if file_identity not in files_by_identity:
                continue
            if files_by_identity[file_identity]["is_link"]:
                links_in_order.append(file_identity)
            else:
                files_in_order.append(file_identity)
        files = []
        for file_identity in prioritized_file_identities:
            file_info = files_by_identity.get(file_identity, {})
            if not file_info:
                continue
            if "text" in file_info:
                del file_info["text"]
            if file_info["is_link"] and not file_info["title"]:
                links_index = links_in_order.index(file_identity)
                file_info["title"] = f"URL {links_index+1}"
            elif not file_info["is_link"] and not file_info["title"] and settings.DEFAULT_FILE_TITLES_TEMPLATE:
                files_index = files_in_order.index(file_identity)
                file_info["title"] = settings.DEFAULT_FILE_TITLES_TEMPLATE.format(ix=files_index+1)
            files.append(file_info)
        data["files"] = files
        # Add contents of files in order to a ContentContainer and create other in-order lists
        licenses = []
        technical_types = []
        for file_identity in prioritized_file_identities:
            file_data = files_by_identity.get(file_identity, {})
            if not file_data:
                continue
            content = Content(
                srn=file_data["srn"],
                provider=file_data["provider"],
                language=get_analyzer_language(file_data.get("language"), as_enum=True),
                title=file_data["title"],
                content=file_data.get("text")
            )
            content_container.append(content)
            if license_ := file_data["copyright"]:
                licenses.append(license_)
            if technical_type := file_data["type"]:
                technical_types.append(technical_type)
        # Return the product with updated data from files
        data["licenses"] = licenses
        data["technical_types"] = technical_types
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

    def transform_search_data(self, data: dict, content: ContentContainer) -> dict:
        text = content.first("content")
        data["suggest_phrase"] = text
        data["suggest_completion"] = self.get_suggest_completion(data["title"], text)
        return data

    def get_derivatives_data(self) -> dict:
        data = super().get_derivatives_data()
        if "study_vocabulary" not in data:
            data["study_vocabulary"] = {}
        if "disciplines_normalized" not in data:
            data["disciplines_normalized"] = {}
        if "consortium" not in data:
            data["consortium"] = {}
        if "publisher_year_normalized" not in data:
            data["publisher_year_normalized"] = None
        return data

    @staticmethod
    def transform_multilingual_fields(data: dict, content: ContentContainer, use_multilingual_fields: bool) -> dict:
        if use_multilingual_fields:
            data["texts"] = content.to_data()
            return data
        # When not using multilingual fields we only transform if we receive a dict for certain fields.
        # The dict indicates that tasks have returned multilingual field data,
        # but caller wants multilingual indices format.
        if isinstance(data["disciplines_normalized"], dict):
            disciplines = data["disciplines_normalized"].get("keyword", [])
            data["disciplines_normalized"] = disciplines
            data["learning_material_disciplines_normalized"] = disciplines
        if isinstance(data["consortium"], dict):
            data["consortium"] = data["consortium"].get("nl")
        if isinstance(data["study_vocabulary"], dict):
            dutch_terms = data["study_vocabulary"].get("nl", [])
            data["study_vocabulary"] = data["study_vocabulary"].get("keyword", [])
            data["study_vocabulary_terms"] = dutch_terms
        data["text"] = content.first("content")
        return data

    def to_data(self, merge_derivatives: bool = True, for_search: bool = True,
                use_multilingual_fields: bool = False) -> dict:
        # Generic transforms
        data = super().to_data(merge_derivatives)
        source, set_name = data["set"].split(":")
        data["harvest_source"] = set_name
        # Add content of the product to a ContentContainer
        product_content = Content(
            srn=data["srn"],
            provider=data["provider"],
            language=get_analyzer_language(data["language"], as_enum=True),
            title=data["title"],
            subtitle=data.get("subtitle"),
            description=data["description"],
        )
        content_container = ContentContainer(contents=[product_content])
        # Transforms based on the files as well as content preparation
        if len(data["files"]):
            data = self.update_files_data(data, content_container)
        else:
            data.update({
                "url": None, "mime_type": None, "previews": None, "video": None,
                "technical_type": data.get("technical_type"),
            })
        # Platform specific transforms
        learning_material = data.pop("learning_material", {})
        if learning_material:
            learning_material.pop("study_vocabulary", None)  # prevents overwriting derivatives data
            if ("consortium" in data and data["consortium"]) or use_multilingual_fields:
                learning_material.pop("consortium", None)  # prevents overwriting derivatives data
            data.update(learning_material)
        research_product = data.pop("research_product", {})
        if research_product:
            research_product.pop("parties", None)  # parties equals publishers for now and we ignore parties
            data.update(research_product)
        # Index related transforms
        data = self.transform_multilingual_fields(
            data, content_container,
            use_multilingual_fields=use_multilingual_fields
        )
        if for_search:
            data = self.transform_search_data(data, content_container)
        # Done
        return data

    def set_metadata(self, current_time=None, new=False) -> None:
        super().set_metadata(current_time=current_time, new=new)
        language = self.metadata.get("language", None)
        if language is None:
            source_language = self.properties.get("language", None)
            self.metadata["language"] = get_analyzer_language(source_language)


class Overwrite(HarvestOverwrite):

    class Meta:
        verbose_name = "product overwrite"
        verbose_name_plural = "product overwrites"
