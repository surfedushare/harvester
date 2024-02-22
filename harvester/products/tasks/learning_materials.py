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
        metadata_values = MetadataValue.objects.filter(
            value__in=document.properties["learning_material"]["study_vocabulary"],
            field__name="study_vocabulary"
        )
        study_vocabulary_terms = set()
        for metadata_value in metadata_values:
            for ancestor in metadata_value.get_ancestors(include_self=True):
                study_vocabulary_terms.add(ancestor.value)
        study_vocabulary_terms = list(study_vocabulary_terms)
        study_vocabulary_terms.sort()
        document.derivatives["lookup_study_vocabulary_parents"] = {
            "study_vocabulary": study_vocabulary_terms
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
            "learning_material_disciplines",
            *document.properties["learning_material"]["disciplines"]
        )
        document.derivatives["normalize_disciplines"] = {
            "learning_material_disciplines_normalized": disciplines_normalized
        }
        # For all documents we mark this task as completed to continue the harvesting process
        document.pipeline["normalize_disciplines"] = {
            "success": True
        }
        document.save()
