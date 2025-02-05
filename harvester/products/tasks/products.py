from django.db.transaction import atomic
from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.loading import load_harvest_models
from metadata.utils.operations import normalize_field_values


@app.task(name="normalize_publisher_year", base=DatabaseConnectionResetTask)
@atomic()
def normalize_publisher_year(app_label: str, document_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    Document = models["Document"]
    for document in Document.objects.filter(id__in=document_ids).select_for_update():
        normalized_publisher_year = normalize_field_values(
            "publisher_year", document.properties["publisher_year"], is_singular=True
        )
        document.derivatives["normalize_publisher_year"] = {"publisher_year_normalized": normalized_publisher_year}
        # For all documents we mark this task as completed to continue the harvesting process
        document.pipeline["normalize_publisher_year"] = {"success": True}
        document.save()
