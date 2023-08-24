from django.db.transaction import atomic
from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.models.datatypes import HarvestSet
from core.tasks.harvest.base import (load_harvest_models, load_pending_harvest_instances, dispatch_harvest_object_tasks,
                                     validate_pending_harvest_instances)
from core.tasks.harvest.dataset_version import dispatch_dataset_version_tasks


@app.task(name="dispatch_set_tasks", base=DatabaseConnectionResetTask)
def dispatch_set_tasks(app_label: str, harvest_set: int | HarvestSet, asynchronous: bool = True,
                       recursion_depth: int = 0) -> None:
    if recursion_depth >= 10:
        raise RecursionError("Maximum harvest_set recursion reached")
    models = load_harvest_models(app_label)
    harvest_set = load_pending_harvest_instances(harvest_set, model=models["Set"])
    pending = validate_pending_harvest_instances(harvest_set, model=models["Set"])
    if len(pending):
        recursive_callback_signature = dispatch_set_tasks.si(
            app_label,
            harvest_set.id,
            asynchronous=asynchronous,
            recursion_depth=recursion_depth+1
        )
        dispatch_harvest_object_tasks(
            app_label,
            *pending,
            callback=recursive_callback_signature,
            asynchronous=asynchronous
        )
    elif validate_pending_harvest_instances(harvest_set.dataset_version, model=models["DatasetVersion"]):
        dataset_version_callback_signature = dispatch_dataset_version_tasks.si(
            app_label,
            harvest_set.dataset_version_id,
            asynchronous=asynchronous,
            recursion_depth=recursion_depth+1
        )
        dispatch_harvest_object_tasks(
            app_label,
            harvest_set.dataset_version,
            callback=dataset_version_callback_signature,
            asynchronous=asynchronous
        )


@app.task(name="apply_set_deletes", base=DatabaseConnectionResetTask)
@atomic()
def apply_set_deletes(app_label: str, set_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    Set = models["Set"]
    for harvest_set in Set.objects.filter(id__in=set_ids).select_for_update():
        harvest_set.pipeline["apply_set_deletes"] = {
            "success": True
        }
        harvest_set.save()


@app.task(name="check_set_integrity", base=DatabaseConnectionResetTask)
@atomic()
def check_set_integrity(app_label: str, set_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    Set = models["Set"]
    for harvest_set in Set.objects.filter(id__in=set_ids).select_for_update():
        harvest_set.pipeline["check_set_integrity"] = {
            "success": True
        }
        harvest_set.save()
