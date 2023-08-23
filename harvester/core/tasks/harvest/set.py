from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.models.datatypes import HarvestSet
from core.tasks.harvest.base import (load_harvest_models, load_pending_harvest_instances, dispatch_harvest_object_tasks,
                                     validate_pending_harvest_instances)
from core.tasks.harvest.dataset_version import harvest_dataset_version


@app.task(name="harvest_set", base=DatabaseConnectionResetTask)
def harvest_set(app_label: str, set_instance: int | HarvestSet, asynchronous: bool = True, recursion_depth: int = 0):
    if recursion_depth >= 10:
        raise RecursionError("Maximum harvest_set recursion reached")
    models = load_harvest_models(app_label)
    set_instance = load_pending_harvest_instances(set_instance, model=models["Set"])
    pending = validate_pending_harvest_instances(set_instance, model=models["Set"])
    if len(pending):
        recursive_callback_signature = harvest_set.si(
            app_label,
            set_instance.id,
            asynchronous=asynchronous,
            recursion_depth=recursion_depth+1
        )
        dispatch_harvest_object_tasks(
            app_label,
            *pending,
            callback=recursive_callback_signature,
            asynchronous=asynchronous
        )
    elif validate_pending_harvest_instances(set_instance.dataset_version, model=models["DatasetVersion"]):
        dataset_version_callback_signature = harvest_dataset_version.si(
            app_label,
            set_instance.dataset_version_id,
            asynchronous=asynchronous,
            recursion_depth=recursion_depth+1
        )
        dispatch_harvest_object_tasks(
            app_label,
            set_instance.dataset_version,
            callback=dataset_version_callback_signature,
            asynchronous=asynchronous
        )
