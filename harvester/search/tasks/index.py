from datetime import datetime

from django.conf import settings
from django.apps import apps
from django.db.transaction import atomic, DatabaseError
from django.utils.timezone import make_aware
from celery import current_app as app, chord
from opensearchpy.exceptions import ConnectionError

from datagrowth.utils.iterators import ibatch
from harvester.tasks.base import DatabaseConnectionResetTask
from core.logging import HarvestLogger
from core.models.datatypes import HarvestDatasetVersion, HarvestDocument
from core.loading import HarvesterDataStorages
from search.models import OpenSearchIndex


@app.task(
    name="index_documents",
    base=DatabaseConnectionResetTask,
    autoretry_for=(ConnectionError,),
    retry_kwargs={'max_retries': 3, 'countdown': 60}
)
@atomic()
def index_documents(app_label: str, dataset_version_id: int, document_ids: list[int]) -> None:
    """
    Index a specific set of documents for a dataset version.

    app_label (str): The app label containing the dataset version
    dataset_version_id (int): The ID of the dataset version
    document_ids (list[int]): List of document IDs to index
    """
    # Load the dataset version and its index
    storages = HarvesterDataStorages.load_instances(f"{app_label}.DatasetVersion", dataset_version_id)
    dataset_version = storages.instance
    if dataset_version is None or dataset_version.index is None:
        return

    # Prepare the logger
    logger = HarvestLogger(
        dataset_version.dataset.name,
        "index_documents",
        command_options={
            "app_label": app_label,
            "dataset_version_id": dataset_version_id,
            "document_count": len(document_ids)
        },
        warn_delete_does_not_exist=False
    )

    # Get documents and process
    logger.debug(f"Starting batch indexing for {len(document_ids)} documents")
    documents = dataset_version.documents.filter(id__in=document_ids)
    enhance_calm = len(document_ids) >= 100
    search_documents = []
    errors = []
    for document in documents:
        if app_label in ["products", "testing"] and not settings.OPENSEARCH_STRICT_MULTILINGUAL_FIELDS:
            language = document.get_analyzer_language()
            search_documents.append((language, document.to_search(use_multilingual_fields=False)))
        search_documents.append(("all", document.to_search(use_multilingual_fields=True)))
    errors += dataset_version.index.push(search_documents, is_done=True, enhance_calm=enhance_calm)

    logger.open_search_errors(errors)


@app.task(name="close_index", base=DatabaseConnectionResetTask)
@atomic()
def close_index(app_label: str, dataset_version_id: int, force_promotion: bool = False) -> None:
    """
    Close and promote an index for a dataset version. This makes the index available for searching
    and marks it as the current version in Postgres.

    app_label: The app label of the entity you want to close index for
    dataset_version_id: The ID of the dataset version
    force_promotion: Whether to promote the index even if it has already been promoted
    """
    # Load the dataset version and its index or exit when nothing should be done.
    storages = HarvesterDataStorages.load_instances(f"{app_label}.DatasetVersion", dataset_version_id, lock=True)
    dataset_version = storages.instance
    if dataset_version is None or dataset_version.index is None:
        return
    elif dataset_version.dataset.indexing == storages.Dataset.IndexingOptions.NO:
        return

    # Prepare the logger
    logger = HarvestLogger(
        dataset_version.dataset.name,
        "close_index",
        command_options={
            "app_label": app_label,
            "dataset_version_id": dataset_version_id,
            "force_promotion": force_promotion
        },
        warn_delete_does_not_exist=False
    )

    # Close the index
    dataset_version.index.close()
    # Only promote if indexing is enabled and set to promote
    if dataset_version.dataset.indexing == storages.Dataset.IndexingOptions.INDEX_AND_PROMOTE:
        logger.info(f"Promoting to latest: {app_label}")
        # We actually perform OpenSearch operations when dealing with a completely new OpenSearchIndex instance.
        if force_promotion or not dataset_version.has_promoted_sibling:
            dataset_version.index.promote_all_to_latest()
        # We update Django's representation of which DatasetVersion represents current data in OpenSearch.
        dataset_version.set_index_promoted()


def _push_dataset_version_to_index(dataset_version: HarvestDatasetVersion, logger: HarvestLogger,
                                   recreate: bool = False, push_since: datetime = None,
                                   batch_size: int = 100, context: str = None) -> OpenSearchIndex | None:
    # Prepare variables.
    errors = []
    current_time = make_aware(datetime.now())
    try:
        with atomic():
            # Load the relevant index and prepare loading Documents.
            index = OpenSearchIndex.objects.select_for_update(nowait=True).get(id=dataset_version.index.id)
            push_since = push_since or index.pushed_at or OpenSearchIndex.objects.get_pushed_at(index.name)
            # See if any Documents match the criteria for pushing to indices.
            filters = {"metadata__modified_at__gte": push_since} if push_since else {}
            if recreate:
                filters["state"] = HarvestDocument.States.ACTIVE
            documents = dataset_version.documents.filter(**filters)
            documents_count = documents.count()
            if not documents_count:
                return index
            # Preparation and batching of documents to push to relevant indices.
            enhance_calm = documents_count >= 100 and not recreate
            logger.info(
                f"Starting batch indexing for {documents_count} {dataset_version._meta.app_label}; "
                f"batch_size={batch_size}, recreate={recreate}, enhance_calm={enhance_calm}, "
                f"push_since={push_since.isoformat() if push_since else "1970-01-01"} "
            )
            index.prepare_push(recreate=recreate)
            for batch in ibatch(documents.iterator(), batch_size):
                search_document_batch = []
                for document in batch:
                    language = document.get_analyzer_language()
                    if index.entity in ["products", "testing"] and not settings.OPENSEARCH_STRICT_MULTILINGUAL_FIELDS:
                        search_document_batch.append((language, document.to_search(use_multilingual_fields=False)))
                    search_document_batch.append(("all", document.to_search(use_multilingual_fields=True)))
                errors += index.push(search_document_batch, is_done=False, enhance_calm=enhance_calm)
            # All documents have been pushed. We'll mark the push as done.
            index.pushed_at = current_time
            index.save()
    except DatabaseError:
        index = None
        message_context = "" if not context else f"for {context}"
        logger.warning(f"Unable to acquire a database lock {message_context}")
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
    _push_dataset_version_to_index(dataset_version, logger, context="sync_opensearch_indices")


@app.task(name="close_index_wrapper", base=DatabaseConnectionResetTask)
def close_index_wrapper(results, app_label: str, dataset_version_id: int, force_promotion: bool = False) -> None:
    """
    Wrapper task that ignores the results from the chord group and calls close_index with the correct parameters.
    """
    return close_index(app_label, dataset_version_id, force_promotion=force_promotion)


@app.task(name="index_dataset_versions", base=DatabaseConnectionResetTask)
def index_dataset_versions(dataset_versions: list[tuple[str, int]], recreate_indices: bool = False,
                           index_since: datetime = None, asynchronous: bool = False,
                           batch_size: int = 100) -> list[str]:
    """
    Index multiple dataset versions, either synchronously or asynchronously.

    Args:
        dataset_versions: List of tuples containing (dataset_version_model, dataset_version_id)
        recreate_indices: Whether to recreate the indices
        index_since: Only index documents modified since this time
        asynchronous: Whether to run the indexing asynchronously
        batch_size: Number of documents to index in a single Celery task

    Returns:
        List of task IDs if any work has been dispatched.
    """
    task_ids = []

    for dataset_version_model, dataset_version_id in dataset_versions:
        # Load the dataset version
        storages = HarvesterDataStorages.load_instances(dataset_version_model, dataset_version_id, lock=True)
        dataset_version = storages.instance
        if dataset_version is None or dataset_version.index is None:
            continue

        # Open the index
        recreate_index = recreate_indices or not dataset_version.has_promoted_sibling
        dataset_version.index.open(recreate=recreate_index)

        # Get all document IDs that need indexing if any
        index_since = index_since or dataset_version.index.pushed_at or \
            OpenSearchIndex.objects.get_pushed_at(dataset_version.index.name)
        filters = {"metadata__modified_at__gte": index_since} if index_since else {}
        if recreate_index:
            filters["state"] = HarvestDocument.States.ACTIVE
        document_ids = list(dataset_version.documents.filter(**filters).values_list('id', flat=True))

        if not document_ids:
            dataset_version.index.close()
            continue

        # Create partial index_documents tasks
        index_tasks = [
            index_documents.s(storages.app_label, dataset_version_id, batch)
            for batch in ibatch(document_ids, batch_size=batch_size)
        ]
        # Create a callback task to close the index after indexing completes
        finish_indexing = close_index_wrapper.s(
            storages.app_label, dataset_version_id, force_promotion=recreate_indices
        )
        # Dispatch the group with callback and collect task ID or execute synchronously
        if asynchronous:
            result = chord(index_tasks)(finish_indexing)
            task_ids.append(result.id)
        else:
            for index_task in index_tasks:
                index_task()
            finish_indexing(None)

    return task_ids
