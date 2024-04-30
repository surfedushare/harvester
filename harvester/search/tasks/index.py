from datetime import datetime

from django.conf import settings
from django.apps import apps
from django.db.transaction import atomic, DatabaseError
from django.utils.timezone import make_aware
from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.logging import HarvestLogger
from core.models.datatypes.dataset import HarvestDatasetVersion
from search.loading import load_data_models
from search.models import OpenSearchIndex


def _push_dataset_version_to_index(dataset_version: HarvestDatasetVersion,
                                   logger: HarvestLogger, recreate: bool = False) -> OpenSearchIndex | None:
    try:
        with atomic():
            index = OpenSearchIndex.objects.select_for_update(nowait=True).get(id=dataset_version.index.id)
            current_time = make_aware(datetime.now())
            filters = {"modified_at__gte": index.pushed_at} if index.pushed_at else {}
            search_documents = dataset_version.get_search_documents_by_language(**filters)
            if not search_documents:
                return
            errors = index.push(search_documents, recreate=recreate)
            logger.open_search_errors(errors)
            index.pushed_at = current_time
            index.save()
    except DatabaseError:
        index = None
        logger.warning("Unable to acquire a database lock for sync_opensearch_indices")
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
def index_dataset_versions(dataset_versions: list[tuple[str, int]], recreate_indices: bool = False) -> None:
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
        index = _push_dataset_version_to_index(dataset_version, logger, recreate=recreate_indices)
        # Switch the aliases to the new indices if required
        if index and dataset_version.dataset.indexing == Dataset.IndexingOptions.INDEX_AND_PROMOTE:
            for language in settings.OPENSEARCH_LANGUAGE_CODES:
                logger.info(f"Promoting to latest: {app_label}, {language}")
                index.promote_to_latest(language)
            dataset_version.set_index_promoted()
