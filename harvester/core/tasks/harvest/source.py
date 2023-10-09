from django.utils.timezone import now
from celery import current_app as app

from datagrowth.utils import ibatch

from harvester.tasks.base import DatabaseConnectionResetTask
from core.loading import load_harvest_models, load_source_configuration
from core.tasks.harvest.document import dispatch_document_tasks
from core.tasks.harvest.set import dispatch_set_tasks
from core.tasks.harvest.dataset_version import dispatch_dataset_version_tasks
from core.processors.seed.resource import HttpSeedingProcessor


@app.task(name="harvest_source", base=DatabaseConnectionResetTask)
def harvest_source(app_label: str, source: str, set_specification: str, asynchronous=True) -> None:
    models = load_harvest_models(app_label)
    configuration = load_source_configuration(app_label, source)
    harvest_state = models["HarvestState"].objects \
        .select_related("entity", "entity__source", "harvest_set") \
        .get(entity__source__module=source, entity__type=app_label, set_specification=set_specification)
    harvest_set = harvest_state.harvest_set

    if harvest_state.entity.is_manual:
        return
    elif harvest_set.pending_at is not None:
        return

    current_time = now()
    has_pending_documents = False

    # Process any documents that already have a pending state due to previous task failures
    for documents in ibatch(harvest_set.documents.filter(pending_at__isnull=False).iterator(), batch_size=20):
        if not len(documents):
            continue
        has_pending_documents = True
        if asynchronous:
            dispatch_document_tasks.delay(app_label, [doc.id for doc in documents], asynchronous=asynchronous)
        else:
            dispatch_document_tasks(app_label, [doc.id for doc in documents], asynchronous=asynchronous)

    # Process new seeds to documents
    seeding_processor = HttpSeedingProcessor(harvest_set, {
        "phases": configuration["seeding_phases"]
    })
    harvest_from = f"{harvest_state.harvested_at:%Y-%m-%dT%H:%M:%SZ}"
    for documents in seeding_processor(harvest_state.set_specification, harvest_from):
        if not len(documents):
            continue
        has_pending_documents = True
        if asynchronous:
            dispatch_document_tasks.delay(app_label, [doc.id for doc in documents], asynchronous=asynchronous)
        else:
            dispatch_document_tasks(app_label, [doc.id for doc in documents], asynchronous=asynchronous)
    else:
        harvest_set.pending_at = current_time if has_pending_documents else None
        harvest_set.clean()
        harvest_set.save()
        if not has_pending_documents:
            if asynchronous:
                dispatch_dataset_version_tasks.delay(app_label, harvest_set.dataset_version_id,
                                                     asynchronous=asynchronous)
            else:
                dispatch_dataset_version_tasks(app_label, harvest_set.dataset_version_id, asynchronous=asynchronous)
        else:
            if asynchronous:
                dispatch_set_tasks.delay(app_label, harvest_set.id, asynchronous=asynchronous)
            else:
                dispatch_set_tasks(app_label, harvest_set.id, asynchronous=asynchronous)

    harvest_state.harvested_at = current_time
    harvest_state.clean()
    harvest_state.save()
