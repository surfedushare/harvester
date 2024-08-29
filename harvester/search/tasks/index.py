from datetime import datetime

from django.apps import apps
from django.db.transaction import atomic, DatabaseError
from django.utils.timezone import make_aware
from celery import current_app as app

from datagrowth.utils.iterators import ibatch
from harvester.tasks.base import DatabaseConnectionResetTask
from core.logging import HarvestLogger
from core.models.datatypes import HarvestDatasetVersion, HarvestDocument
from search.loading import load_data_models
from search.models import OpenSearchIndex


def _push_dataset_version_to_index(dataset_version: HarvestDatasetVersion,
                                   logger: HarvestLogger, recreate: bool = False,
                                   push_since: datetime = None, batch_size: int = 100) -> OpenSearchIndex | None:
    # Prepare variables.
    errors = []
    current_time = make_aware(datetime.now())
    try:
        with atomic():
            # Load the relevant index and prepare loading Documents.
            index = OpenSearchIndex.objects.select_for_update(nowait=True).get(id=dataset_version.index.id)
            push_since = push_since or index.pushed_at
            # See if any Documents match the criteria for pushing to indices.
            filters = {"metadata__modified_at__gte": push_since} if push_since else {}
            if recreate:
                filters["state"] = HarvestDocument.States.ACTIVE
            documents = dataset_version.documents.filter(**filters)
            if not documents.exists():
                return
            # Preparation and batching of documents to push to relevant indices.
            index.prepare_push(recreate=recreate)
            for batch in ibatch(documents, batch_size):
                search_document_batch = []
                for document in batch:
                    language = document.get_analyzer_language()
                    search_document_batch.append((language, document.to_search(use_multilingual_fields=False)))
                    search_document_batch.append(("all", document.to_search(use_multilingual_fields=False)))
                errors += index.push(search_document_batch, is_done=False)
            # All documents have been pushed. We'll mark the push as done.
            index.pushed_at = current_time
            index.save()
    except DatabaseError:
        index = None
        logger.warning("Unable to acquire a database lock for sync_opensearch_indices")
    logger.open_search_errors(errors)
    return index


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
    logger = HarvestLogger(
        dataset_version.dataset.name,
        "sync_opensearch_indices",
        command_options={
            "app_label": app_label
        },
        is_legacy_logger=False,
        warn_delete_does_not_exist=False
    )

    # Acquire lock and push recently modified documents to the index
    _push_dataset_version_to_index(dataset_version, logger)


@app.task(name="index_dataset_versions", base=DatabaseConnectionResetTask)
def index_dataset_versions(dataset_versions: list[tuple[str, int]], recreate_indices: bool = False,
                           index_since: datetime = None) -> None:
    index_since = index_since if not recreate_indices else make_aware(datetime(year=1970, month=1, day=1))
    for dataset_version_model, dataset_version_id in dataset_versions:
        # Load the dataset version
        Dataset, DatasetVersion, dataset_version = load_data_models(dataset_version_model, dataset_version_id)
        if dataset_version is None or dataset_version.index is None:
            continue
        # Prepare the logger
        app_label = DatasetVersion._meta.app_label
        logger = HarvestLogger(
            dataset_version.dataset.name, "index_dataset_versions",
            command_options={
                "app_label": app_label,
                "model_name": DatasetVersion._meta.model_name,
                "instance_id": dataset_version_id
            },
            is_legacy_logger=False,
            warn_delete_does_not_exist=False
        )
        # Acquire lock and push recently modified documents to the index
        logger.info(f"Pushing index for: {app_label}")
        index = _push_dataset_version_to_index(
            dataset_version, logger,
            recreate=recreate_indices, push_since=index_since
        )
        # Switch the aliases to the new indices if required
        if index and dataset_version.dataset.indexing == Dataset.IndexingOptions.INDEX_AND_PROMOTE:
            logger.info(f"Promoting to latest: {app_label}")
            index.promote_all_to_latest()
            dataset_version.set_index_promoted()
