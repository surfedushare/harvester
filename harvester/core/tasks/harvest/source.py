from django.utils.timezone import now
from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.tasks.harvest.base import load_harvest_models, load_source_configuration
from core.tasks.harvest.document import harvest_documents
from core.tasks.harvest.set import harvest_set
from core.processors.seed.resource import HttpSeedingProcessor


@app.task(name="harvest_source", base=DatabaseConnectionResetTask)
def harvest_source(app_label: str, source: str, asynchronous=True):
    models = load_harvest_models(app_label)
    configuration = load_source_configuration(app_label, source)
    harvest_state = models["HarvestState"].objects \
        .select_related("entity", "entity__source", "harvest_set") \
        .get(entity__source__module=source, entity__type=app_label)
    state_set = harvest_state.harvest_set

    if harvest_state.entity.is_manual:
        return
    elif state_set.pending_at is not None:
        return

    current_time = now()
    seeding_processor = HttpSeedingProcessor(state_set, {
        "phases": configuration["seeding_phases"]
    })
    has_seeds = False
    harvest_from = f"{harvest_state.harvested_at:%Y-%m-%dT%H:%M:%SZ}"
    for documents in seeding_processor(harvest_state.entity.set_specification, harvest_from):
        has_seeds = True
        harvest_documents(app_label, [doc.id for doc in documents], asynchronous=asynchronous)
    else:
        state_set.pending_at = current_time
        state_set.clean()
        state_set.save()
        harvest_set(app_label, state_set.id, asynchronous=asynchronous)

    if not has_seeds:
        state_set.pending_at = None

    state_set.harvested_at = current_time
    state_set.clean()
    state_set.save()
