from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.models.datatypes import HarvestDocument, HarvestSet
from core.tasks.harvest.base import (load_harvest_models, load_pending_harvest_instances, dispatch_harvest_object_tasks,
                                     validate_pending_harvest_instances)


@app.task(name="harvest_documents", base=DatabaseConnectionResetTask)
def harvest_documents(app_label: str, documents: list[int | HarvestDocument],
                      asynchronous: bool = True, recursion_depth: int = 0):
    if recursion_depth >= 10:
        raise RecursionError("Maximum harvest_documents recursion reached")
    models = load_harvest_models(app_label)
    documents = load_pending_harvest_instances(*documents, model=models["Document"], as_list=True)
    pending = validate_pending_harvest_instances(documents, model=models["Document"])
    if len(pending):
        recursive_callback_signature = harvest_documents.si(
            app_label,
            [doc.id for doc in documents],
            asynchronous=asynchronous,
            recursion_depth=recursion_depth+1
        )
        dispatch_harvest_object_tasks(
            app_label,
            *pending,
            callback=recursive_callback_signature,
            asynchronous=asynchronous
        )
