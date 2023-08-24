from collections import defaultdict

from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.loading import load_harvest_models
from core.tasks.harvest.source import harvest_source
from sources.models.harvest import HarvestEntity


@app.task(name="harvest_entities", base=DatabaseConnectionResetTask)
def harvest_entities(entity: str = None, reset: bool = False, asynchronous: bool = True) -> None:
    if entity:
        entities = HarvestEntity.objects.select_related("source").filter(type=entity, is_available=True)
    else:
        entities = HarvestEntity.objects.select_related("source").filter(is_available=True)
    datasets = defaultdict(list)
    for entity in entities:
        models = load_harvest_models(entity.type)
        Dataset = models["Dataset"]
        HarvestState = models["HarvestState"]
        for dataset in Dataset.objects.filter(is_harvested=True):
            state, created = HarvestState.objects.get_or_create(entity=entity, dataset=dataset)
            datasets[dataset].append(state)

    for dataset, states in datasets.items():
        current_version = dataset.versions.get_current_version()
        new_version = dataset.versions.create()
        for state in states:
            if reset or not current_version:
                state.clear_resources()
                state.reset(new_version)
            else:
                current_set = current_version.collections.get(name=state.set_name)
                new_version.historic_sets.add(current_set)
                state.prepare_using_set(current_set)
            harvest_source(state.entity.type, state.entity.source.module, asynchronous=asynchronous)
