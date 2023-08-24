from django.db.transaction import atomic
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


@app.task(name="apply_set_deletes", base=DatabaseConnectionResetTask)
@atomic()
def apply_set_deletes(app_label: str, set_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    Set = models["Set"]
    for set_instance in Set.objects.filter(id__in=set_ids).select_for_update():
        set_instance.pipeline["apply_set_deletes"] = {
            "success": True
        }
        set_instance.save()


@app.task(name="check_set_integrity", base=DatabaseConnectionResetTask)
@atomic()
def check_set_integrity(app_label: str, set_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    Set = models["Set"]
    for set_instance in Set.objects.filter(id__in=set_ids).select_for_update():
        set_instance.pipeline["check_set_integrity"] = {
            "success": True
        }
        set_instance.save()
