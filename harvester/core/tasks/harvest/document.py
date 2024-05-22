from django.utils.timezone import now
from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.loading import load_harvest_models
from core.logging import HarvestLogger
from core.models.datatypes import HarvestDocument
from core.tasks.harvest.base import (load_pending_harvest_instances, dispatch_harvest_object_tasks,
                                     validate_pending_harvest_instances)


@app.task(name="harvest_documents", base=DatabaseConnectionResetTask)
def dispatch_document_tasks(app_label: str, documents: list[int | HarvestDocument], asynchronous: bool = True,
                            recursion_depth: int = 0) -> None:
    if not len(documents):
        return
    if recursion_depth >= 10:
        raise RecursionError("Maximum harvest_documents recursion reached")
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
            document.pipeline[task] = {"success": False, "canceled": True}
        document.pending_at = None
        document.finished_at = now()
        stopped.append(document)

    models["Document"].objects.bulk_update(stopped, ["pending_at", "finished_at", "pipeline"])

    if stopped:
        dataset_version = stopped[0].dataset_version
        collection = stopped[0].collection
        dataset = dataset_version.dataset.name if dataset_version else None
        source = collection.name if collection else None
        logger = HarvestLogger(dataset, "cancel_document_tasks", {}, is_legacy_logger=False)
        logger.report_cancelled_documents(app_label, source, len(stopped))
