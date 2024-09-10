from django.db.transaction import atomic
from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.loading import load_harvest_models
from metadata.models import MetadataValue
from metadata.utils.operations import normalize_field_values


@app.task(name="lookup_study_vocabulary_parents", base=DatabaseConnectionResetTask)
@atomic()
def lookup_study_vocabulary_parents(app_label: str, document_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    Document = models["Document"]
    for document in Document.objects.filter(id__in=document_ids).select_for_update():
        metadata_values = MetadataValue.objects.select_related("translation").filter(
            value__in=document.properties["learning_material"]["study_vocabulary"],
            field__name="study_vocabulary"
        )
        study_vocabulary_ids = set()
        study_vocabulary_nl = set()
        study_vocabulary_en = set()
        for metadata_value in metadata_values:
            for ancestor in metadata_value.get_ancestors(include_self=True):
                study_vocabulary_ids.add(ancestor.value)
                study_vocabulary_nl.add(ancestor.translation.nl)
                study_vocabulary_en.add(ancestor.translation.en)
        study_vocabulary_ids = list(study_vocabulary_ids)
        study_vocabulary_ids.sort()
        study_vocabulary_nl = list(study_vocabulary_nl)
        study_vocabulary_nl.sort()
        study_vocabulary_en = list(study_vocabulary_en)
        study_vocabulary_en.sort()
        document.derivatives["lookup_study_vocabulary_parents"] = {
            "study_vocabulary": {
                "keyword": study_vocabulary_ids,
                "nl": study_vocabulary_nl,
                "en": study_vocabulary_en,
            }
        }
        # For all documents we mark this task as completed to continue the harvesting process
        document.pipeline["lookup_study_vocabulary_parents"] = {
            "success": True
        }
        document.save()


@app.task(name="normalize_disciplines", base=DatabaseConnectionResetTask)
@atomic()
def normalize_disciplines(app_label: str, document_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    Document = models["Document"]
    for document in Document.objects.filter(id__in=document_ids).select_for_update():
        disciplines_normalized = normalize_field_values(
            "disciplines",
            *document.properties["learning_material"]["disciplines"],
            as_models=True
        )
        document.derivatives["normalize_disciplines"] = {
            "disciplines_normalized": {
                "keyword": [discipline.value for discipline in disciplines_normalized],
                "nl": [discipline.translation.nl for discipline in disciplines_normalized],
                "en": [discipline.translation.en for discipline in disciplines_normalized],
            }
        }
        # For all documents we mark this task as completed to continue the harvesting process
        document.pipeline["normalize_disciplines"] = {
            "success": True
        }
        document.save()


@app.task(name="lookup_consortium_translations", base=DatabaseConnectionResetTask)
@atomic()
def lookup_consortium_translations(app_label: str, document_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    Document = models["Document"]
    for document in Document.objects.filter(id__in=document_ids).select_for_update():
        consortium_value = MetadataValue.objects \
            .select_related("translation") \
            .filter(value=document.properties["learning_material"]["consortium"]) \
            .last()
        default_consortium = document.properties.get("learning_material").get("consortium")
        document.derivatives["lookup_consortium_translations"] = {
            "consortium": {
                "keyword": consortium_value.value if consortium_value else default_consortium,
                "nl": consortium_value.translation.nl if consortium_value else None,
                "en": consortium_value.translation.en if consortium_value else None
            }
        }
        # For all documents we mark this task as completed to continue the harvesting process
        document.pipeline["lookup_consortium_translations"] = {
            "success": True
        }
        document.save()
