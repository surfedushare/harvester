from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.models import DatasetVersion
from core.tasks.harvest.base import (load_harvest_models, load_pending_harvest_instances, dispatch_harvest_object_tasks,
                                     validate_pending_harvest_instances)


@app.task(name="harvest_dataset_version", base=DatabaseConnectionResetTask)
def harvest_dataset_version(app_label: str, dataset_version: int | DatasetVersion, asynchronous: bool = True,
                            recursion_depth: int = 0):
    if recursion_depth >= 10:
        raise RecursionError("Maximum harvest_dataset_version recursion reached")
    models = load_harvest_models(app_label)
    dataset_version = load_pending_harvest_instances(dataset_version, model=models["DatasetVersion"])
    pending = validate_pending_harvest_instances(dataset_version, model=models["Set"])
    if len(pending):
        recursive_callback_signature = harvest_dataset_version.si(
            app_label,
            dataset_version.id,
            asynchronous=asynchronous,
            recursion_depth=recursion_depth+1
        )
        dispatch_harvest_object_tasks(
            *pending,
            callback=recursive_callback_signature,
            asynchronous=asynchronous
        )
