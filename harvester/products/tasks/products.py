from django.apps import apps
from django.db.transaction import atomic
from celery import current_app as app
import pydantic

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


@app.task(name="deactivate_invalid_products", base=DatabaseConnectionResetTask)
@atomic()
def deactivate_invalid_products(app_label: str, document_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    Document = models["Document"]
    app_config = apps.get_app_config(app_label)
    Validator = app_config.result_transformer
    for document in Document.objects.filter(id__in=document_ids).select_for_update():
        try:
            Validator(**document.to_data(merge_derivatives=True))
            validation_output = None
        except pydantic.ValidationError as exc:
            document.state = document.States.INACTIVE
            validation_output = str(exc)
        # For all documents we mark this task as completed to continue the harvesting process
        document.pipeline["deactivate_invalid_products"] = {
            "success": True,
            "validation": validation_output,
        }
        document.save()
