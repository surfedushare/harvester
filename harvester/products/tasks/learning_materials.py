from django.db.transaction import atomic
from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.loading import load_harvest_models


@app.task(name="lookup_study_vocabulary_parents", base=DatabaseConnectionResetTask)
@atomic()
def lookup_study_vocabulary_parents(app_label: str, document_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    Document = models["Document"]
    for document in Document.objects.filter(id__in=document_ids).select_for_update():
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
        # For all documents we mark this task as completed to continue the harvesting process
        document.pipeline["normalize_disciplines"] = {
            "success": True
        }
        document.save()
