from django.utils.timezone import now
from celery import current_app as app

from datagrowth.utils import ibatch

from harvester.tasks.base import DatabaseConnectionResetTask
from core.loading import load_harvest_models, load_source_configuration
from core.logging import HarvestLogger
from core.tasks.harvest.document import dispatch_document_tasks
from core.tasks.harvest.set import start_set_processing
from core.processors.seed.resource import HttpSeedingProcessor


@app.task(name="harvest_source", base=DatabaseConnectionResetTask)
def harvest_source(app_label: str, source: str, set_specification: str, asynchronous=True) -> None:
    current_time = now()
    models = load_harvest_models(app_label)
    configuration = load_source_configuration(app_label, source)
    logger_options = {
        "source": source,
        "set_specification": set_specification
    }
    logger = HarvestLogger(app_label, "harvest_source", logger_options, is_legacy_logger=False)
    harvest_state = models["HarvestState"].objects \
        .select_related("entity", "entity__source", "harvest_set") \
        .get(entity__source__module=source, entity__type=app_label, set_specification=set_specification)
    harvest_set = harvest_state.harvest_set

    if harvest_state.entity.is_manual:
        logger.info(f"The '{harvest_state.entity}' operates in manual mode and won't harvest new documents")
        start_set_processing(harvest_set, current_time, asynchronous=asynchronous)
        return
    elif harvest_set.pending_at is not None:
        logger.warning(
            f"Set '{harvest_set.name}' is already pending since {harvest_set.pending_at} and will not harvest again"
        )
        return

    # Process any documents that already have a pending state due to previous task failures
    for documents in ibatch(harvest_set.documents.filter(pending_at__isnull=False).iterator(), batch_size=20):
        if not len(documents):
            continue
        if asynchronous:
            dispatch_document_tasks.delay(app_label, [doc.id for doc in documents], asynchronous=asynchronous)
        else:
            dispatch_document_tasks(app_label, [doc.id for doc in documents], asynchronous=asynchronous)
        for doc in documents:
            logger.report_document(
                doc.identity,
                app_label,
                state=doc.state,
                title=doc.properties.get("title", None)
            )

    # Process new seeds to documents
    seeding_processor = HttpSeedingProcessor(harvest_set, {
        "phases": configuration["seeding_phases"]
    })
    harvest_from = f"{harvest_state.harvested_at:%Y-%m-%dT%H:%M:%SZ}"
    for documents in seeding_processor(harvest_state.set_specification, harvest_from):
        documents = [doc for doc in documents if doc.pending_at]
        if not len(documents):
            continue
        if asynchronous:
            dispatch_document_tasks.delay(app_label, [doc.id for doc in documents], asynchronous=asynchronous)
        else:
            dispatch_document_tasks(app_label, [doc.id for doc in documents], asynchronous=asynchronous)
        for doc in documents:
            logger.report_document(
                doc.identity,
                app_label,
                state=doc.state,
                title=doc.properties.get("title", None)
            )
    else:
        logger.info(f"Finished seeding for: {app_label}, {harvest_set.name}")
        logger.report_collection(harvest_set, app_label)
        start_set_processing(harvest_set, current_time, asynchronous=asynchronous)

    harvest_state.harvested_at = current_time
    harvest_state.clean()
    harvest_state.save()
