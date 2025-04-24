from time import sleep

from django.apps import apps
from django.db.transaction import atomic
from django.utils.timezone import now
from celery import current_app as app
import pydantic

from harvester.tasks.base import DatabaseConnectionResetTask
from core.loading import load_harvest_models
from core.models.datatypes import HarvestDocument
from core.tasks.harvest.base import (load_pending_harvest_instances, dispatch_harvest_object_tasks,
                                     validate_pending_harvest_instances)


@app.task(name="harvest_documents", base=DatabaseConnectionResetTask)
def dispatch_document_tasks(app_label: str, documents: list[int | HarvestDocument], asynchronous: bool = True,
                            recursion_depth: int = 0) -> None:
    if not len(documents):
        return
    elif recursion_depth >= 10:
        raise RecursionError("Maximum harvest_documents recursion reached")
    elif recursion_depth % 2:
        # Give system/cloud a bit of time to process documents fully
        sleep(recursion_depth)

    models = load_harvest_models(app_label)
    documents = load_pending_harvest_instances(*documents, model=models["Document"], as_list=True)
    pending = validate_pending_harvest_instances(documents, model=models["Document"])

    if len(pending):
        recursive_callback_signature = dispatch_document_tasks.si(
            app_label,
            [doc.id for doc in pending],
            asynchronous=asynchronous,
            recursion_depth=recursion_depth+1
        )
        dispatch_harvest_object_tasks(
            app_label,
            *pending,
            callback=recursive_callback_signature,
            asynchronous=asynchronous
        )


@app.task(name="cancel_document_tasks", base=DatabaseConnectionResetTask)
def cancel_document_tasks(app_label: str, documents: list[int | HarvestDocument]) -> None:
    if not len(documents):
        return
    models = load_harvest_models(app_label)
    documents = load_pending_harvest_instances(*documents, model=models["Document"], as_list=True)
    if not documents:
        return
    documents = documents if isinstance(documents, list) else [documents]
    stopped = []
    for document in documents:
        for task in document.get_pending_tasks():
            document.task_results[task] = {"success": False, "canceled": True}
        document.pending_at = None
        document.finished_at = now()
        stopped.append(document)

    models["Document"].objects.bulk_update(stopped, ["pending_at", "finished_at", "task_results"])


@app.task(name="deactivate_invalid_documents", base=DatabaseConnectionResetTask)
@atomic()
def deactivate_invalid_documents(app_label: str, document_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    Document = models["Document"]
    app_config = apps.get_app_config(app_label)
    Validator = app_config.result_transformer
    for document in Document.objects.filter(id__in=document_ids).select_for_update():
        try:
            Validator(**document.to_data(merge_derivatives=True))
            validation_output = None
        except pydantic.ValidationError as exc:
            validation_output = str(exc)
        # For all documents we mark this task as completed to continue the harvesting process
        document.task_results["deactivate_invalid_documents"] = {
            "success": True,
            "validation": validation_output,
        }
        document.clean()
        document.save()
