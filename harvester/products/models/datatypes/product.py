from django.db import models
from django.conf import settings

from core.models.datatypes import HarvestDocument, HarvestOverwrite
from metadata.models import MetadataValue


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


class Overwrite(HarvestOverwrite):

    class Meta:
        verbose_name = "product overwrite"
        verbose_name_plural = "product overwrites"
