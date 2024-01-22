import logging
from datetime import datetime

from django.db.transaction import atomic
from celery import current_app as app

from datagrowth.utils import ibatch
from harvester.tasks.base import DatabaseConnectionResetTask
from core.loading import load_harvest_models
from core.models.datatypes import HarvestSet
from core.tasks.harvest.base import (load_pending_harvest_instances, dispatch_harvest_object_tasks,
                                     validate_pending_harvest_instances, PendingHarvestObjects)
from core.tasks.harvest.dataset_version import dispatch_dataset_version_tasks
from core.tasks.harvest.document import cancel_document_tasks


logger = logging.getLogger("harvester")


def dispatch_set_task_retry(task, exc, task_id, args, kwargs, einfo):
    if task.request.retries == task.max_retries:
        app_label = args[0]
        harvest_set_id = args[1]
        models = load_harvest_models(app_label)
        harvest_set = load_pending_harvest_instances(harvest_set_id, model=models["Set"])
        if harvest_set is None:
            logger.warning("Couldn't load pending Set during on_retry of dispatch_set_tasks")
            return
        pending_document_count = harvest_set.documents.filter(pending_at__isnull=False).count()
        logger.info(f"Cancelling document tasks for {pending_document_count} documents")
        for batch in ibatch(harvest_set.documents.filter(pending_at__isnull=False).iterator(), batch_size=100):
            cancel_document_tasks(app_label, batch)


@app.task(
    name="dispatch_set_tasks",
    base=DatabaseConnectionResetTask,
    autoretry_for=(PendingHarvestObjects,),
    retry_kwargs={"max_retries": 5, "countdown": 5 * 60},
    on_retry=dispatch_set_task_retry
)
def dispatch_set_tasks(app_label: str, harvest_set: int | HarvestSet, asynchronous: bool = True,
                       recursion_depth: int = 0) -> None:
    if recursion_depth >= 10:
        raise RecursionError("Maximum harvest_set recursion reached")
    models = load_harvest_models(app_label)
    harvest_set = load_pending_harvest_instances(harvest_set, model=models["Set"])
    if harvest_set is None:  # parallel tasks may already picked-up this dispatch
        return
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


def start_set_processing(harvest_set: HarvestSet, start_time: datetime, asynchronous: bool = True) -> None:
    """
    A convenience function that sets the state of Set to pending and starts background task dispatcher.

    :param harvest_set: the Set that should start processing tasks
    :param start_time: the time the Set should be considered pending
    :param asynchronous: whether to process the set asynchronously
    :return: None
    """
    harvest_set.pending_at = start_time
    harvest_set.clean()
    harvest_set.save()
    app_label = harvest_set._meta.app_label
    if asynchronous:
        dispatch_set_tasks.delay(app_label, harvest_set.id, asynchronous=asynchronous)
    else:
        dispatch_set_tasks(app_label, harvest_set.id, asynchronous=asynchronous)


@app.task(name="check_set_integrity", base=DatabaseConnectionResetTask)
@atomic()
def check_set_integrity(app_label: str, set_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    Set = models["Set"]
    for harvest_set in Set.objects.filter(id__in=set_ids).select_for_update():
        # The check_set_integrity call may replace new data with historic data when validation fails
        is_replaced = False
        # Historic data needs to be larger than 50 documents before we consider replacement
        historic_set = harvest_set.dataset_version.historic_sets.filter(name=harvest_set.name).last()
        if historic_set is not None and historic_set.documents.count() >= 50:
            historic_count = historic_set.documents.filter(metadata__deleted_at=None).count()
            current_count = harvest_set.documents.filter(metadata__deleted_at=None).count()
            count_diff = historic_count - current_count
            # If historic data is 5% larger than new data the data is considered invalid
            # We'll use the historic data instead of the new data
            if current_count == 0 or (count_diff > 0 and count_diff / current_count >= 0.05):
                is_replaced = True
                harvest_set.documents.all().delete()
                harvest_set.copy_documents(historic_set)
        # For all sets we mark this task as completed to continue the harvesting process
        harvest_set.pipeline["check_set_integrity"] = {
            "success": True,
            "is_replaced": is_replaced
        }
        harvest_set.save()
