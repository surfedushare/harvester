from datetime import datetime

from django.apps import apps
from django.db.transaction import atomic, DatabaseError
from django.utils.timezone import make_aware
from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.logging import HarvestLogger
from search.models import OpenSearchIndex


@app.task(name="sync_opensearch_indices", base=DatabaseConnectionResetTask)
def sync_opensearch_indices(app_label: str) -> None:
    # Load current DatasetVersion instance and check validity
    DatasetVersion = apps.get_model(f"{app_label}.DatasetVersion")
    Dataset = apps.get_model(f"{app_label}.Dataset")
    dataset_version = DatasetVersion.objects.get_current_version()
    # Can't index if dataset version or its index doesn't exist at all
    if dataset_version is None or dataset_version.index is None:
        return
    # Won't index if index hasn't been pushed yet or dataset doesn't require indexing
    if dataset_version.index.pushed_at is None or dataset_version.dataset.indexing == Dataset.IndexingOptions.NO:
        return

    # Prepare the logger
    logger = HarvestLogger(dataset_version.dataset.name, "sync_opensearch_indices", {
        "app_label": app_label
    })

    # Acquire lock and push recently modified documents to the index
    try:
        with atomic():
            index = OpenSearchIndex.objects.select_for_update(nowait=True).get(id=dataset_version.index.id)
            current_time = make_aware(datetime.now())
            search_documents = dataset_version.get_search_documents_by_language(modified_at__gte=index.pushed_at)
            if not search_documents:
                return
            errors = index.push(search_documents, recreate=False)
            logger.open_search_errors(errors)
            index.pushed_at = current_time
            index.save()
    except DatabaseError:
        logger.warning("Unable to acquire a database lock for sync_opensearch_indices")
