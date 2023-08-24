from django.db.transaction import atomic
from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.models import DatasetVersion
from core.tasks.harvest.base import (load_harvest_models, load_pending_harvest_instances, dispatch_harvest_object_tasks,
                                     validate_pending_harvest_instances)


@app.task(name="harvest_dataset_version", base=DatabaseConnectionResetTask)
def dispatch_dataset_version_tasks(app_label: str, dataset_version: int | DatasetVersion, asynchronous: bool = True,
                                   recursion_depth: int = 0) -> None:
    if recursion_depth >= 10:
        raise RecursionError("Maximum harvest_dataset_version recursion reached")
    models = load_harvest_models(app_label)
    dataset_version = load_pending_harvest_instances(dataset_version, model=models["DatasetVersion"])
    pending = validate_pending_harvest_instances(dataset_version, model=models["DatasetVersion"])
    if len(pending):
        recursive_callback_signature = dispatch_dataset_version_tasks.si(
            app_label,
            dataset_version.id,
            asynchronous=asynchronous,
            recursion_depth=recursion_depth+1
        )
        dispatch_harvest_object_tasks(
            app_label,
            *pending,
            callback=recursive_callback_signature,
            asynchronous=asynchronous
        )


@app.task(name="push_to_index", base=DatabaseConnectionResetTask)
@atomic
def push_to_index(app_label, dataset_version_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    DatasetVersion = models["DatasetVersion"]
    for dataset_version in DatasetVersion.objects.filter(id__in=dataset_version_ids).select_for_update():
        dataset_version.pipeline["push_to_index"] = {
            "success": True
        }
        dataset_version.save()
