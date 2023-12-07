from django.apps import apps
from django.db.transaction import atomic
from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.loading import load_harvest_models
from core.models import DatasetVersion
from core.tasks.harvest.base import (load_pending_harvest_instances, dispatch_harvest_object_tasks,
                                     validate_pending_harvest_instances, PendingHarvestObjects)


@app.task(
    name="harvest_dataset_version",
    base=DatabaseConnectionResetTask,
    autoretry_for=(PendingHarvestObjects,),
    retry_kwargs={"max_retries": 5, "countdown": 5 * 60}
)
def dispatch_dataset_version_tasks(app_label: str, dataset_version: int | DatasetVersion, asynchronous: bool = True,
                                   recursion_depth: int = 0, previous_tasks: list[str] = None) -> None:
    if recursion_depth >= 10:
        raise RecursionError("Maximum harvest_dataset_version recursion reached")
    previous_tasks = previous_tasks or []
    # Load DatasetVersion and check its state
    models = load_harvest_models(app_label)
    dataset_version = load_pending_harvest_instances(dataset_version, model=models["DatasetVersion"])
    if dataset_version is None:  # parallel tasks may already picked-up this dispatch
        return

    # Dispatch pending tasks
    pending = validate_pending_harvest_instances(dataset_version, model=models["DatasetVersion"])
    pending_tasks = [task for instance in pending for task in instance.get_pending_tasks()]
    if len(pending) and pending_tasks != previous_tasks:  # we're not repeating the same tasks indefinitely
        recursive_callback_signature = dispatch_dataset_version_tasks.si(
            app_label,
            dataset_version.id,
            asynchronous=asynchronous,
            recursion_depth=recursion_depth+1,
            previous_tasks=pending_tasks
        )
        dispatch_harvest_object_tasks(
            app_label,
            *pending,
            callback=recursive_callback_signature,
            asynchronous=asynchronous
        )


@app.task(name="set_current_dataset_version", base=DatabaseConnectionResetTask)
@atomic
def set_current_dataset_version(app_label: str, dataset_version_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    DatasetVersion = models["DatasetVersion"]
    for dataset_version in DatasetVersion.objects.filter(id__in=dataset_version_ids).select_for_update():
        # A Set is unfinished when it is not yet pending (because Documents are still coming in),
        # but any tasks for the set haven't run either
        has_unfinished_sets = dataset_version.sets.filter(finished_at__isnull=True).exists()
        # A set will become pending when all Documents have been fetched and stored
        # and will remain pending as long as not all tasks have been completed
        has_pending_sets = dataset_version.sets.filter(pending_at__isnull=False).exists()
        # We only want to set the DatasetVersion to become "current",
        # meaning all output including indexing will use this DatasetVersion,
        # when all tasks for all sets have executed
        should_set_current = not has_unfinished_sets and not has_pending_sets
        if should_set_current:
            dataset_version.set_current()
            dataset_version.pipeline["set_current_dataset_version"] = {"success": True}
            dataset_version.save()


@app.task(name="create_opensearch_index", base=DatabaseConnectionResetTask)
@atomic
def create_opensearch_index(app_label: str, dataset_version_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    DatasetVersion = models["DatasetVersion"]
    OpenSearchIndex = apps.get_model("search.OpenSearchIndex")
    for dataset_version in DatasetVersion.objects.filter(id__in=dataset_version_ids).select_for_update():
        if dataset_version.dataset.indexing != models["Dataset"].IndexingOptions.NO:
            dataset_version.index = OpenSearchIndex.build(
                app_label,
                dataset_version.dataset.name,
                dataset_version.version
            )
            dataset_version.index.save()
        dataset_version.pipeline["create_opensearch_index"] = {"success": True}
        dataset_version.save()
