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
    def has_study_vocabulary(self):
        study_vocabulary_ids = self.properties.get("learning_material", {}).get("study_vocabulary", [])
        if not study_vocabulary_ids:
            return False
        return MetadataValue.objects.filter(field__name="study_vocabulary", value__in=study_vocabulary_ids).exists()

    @property
    def has_disciplines(self):
        discipline_ids = self.properties.get("learning_material", {}).get("disciplines", [])
        if not discipline_ids:
            return False
        return MetadataValue.objects \
            .filter(field__name="learning_material_disciplines_normalized", value__in=discipline_ids) \
            .exists()

    @staticmethod
    def update_files_data(data: dict) -> dict:
        file_identities = [
            f"{data['set']}:{sha1(url.encode('utf-8')).hexdigest()}"
            for url in data["files"]
        ]
        files_by_identity = {
            file_document.identity: file_document.to_data()
            for file_document in FileDocument.objects.filter(identity__in=file_identities, is_not_found=False)
        }
        first_file_document = files_by_identity[file_identities[0]]
        main_file_info = {
            "url": first_file_document["url"],
            "mime_type": first_file_document["mime_type"],
            "technical_type": first_file_document["type"]
        }
        data.update(main_file_info)
        links_in_order = [
            file_identity for file_identity in file_identities
            if files_by_identity[file_identity]["is_link"]
        ]
        files = []
        for file_identity in file_identities:
            file_info = files_by_identity.get(file_identity, None)
            if not file_info:
                continue
            if file_info["is_link"] and not file_info["title"]:
                links_index = links_in_order.index(file_identity)
                file_info["title"] = f"URL {links_index+1}"
            files.append(file_info)
        data["files"] = files
        return data

    def to_data(self, merge_derivatives: bool = True) -> dict:
        data = super().to_data(merge_derivatives)
        if len(data["files"]):
            data = self.update_files_data(data)
        return data


class Overwrite(HarvestOverwrite):

    class Meta:
        verbose_name = "product overwrite"
        verbose_name_plural = "product overwrites"
