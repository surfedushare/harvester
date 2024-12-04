from django.apps import apps
from django.db.transaction import atomic
from celery import current_app as app
import pydantic

from harvester.tasks.base import DatabaseConnectionResetTask
from core.loading import load_harvest_models


@app.task(name="deactivate_invalid_organizations", base=DatabaseConnectionResetTask)
@atomic()
def deactivate_invalid_organizations(app_label: str, document_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    Document = models["Document"]
    app_config = apps.get_app_config(app_label)
    Validator = app_config.result_transformer
    for document in Document.objects.filter(id__in=document_ids).select_for_update():
        try:
            Validator(**document.to_data(merge_derivatives=True))
            validation_output = None
        except pydantic.ValidationError as exc:
            document.properties["state"] = document.States.INACTIVE
            validation_output = str(exc)
        # For all documents we mark this task as completed to continue the harvesting process
        document.pipeline["deactivate_invalid_organizations"] = {
            "success": True,
            "validation": validation_output,
        }
        document.clean()
        document.save()
