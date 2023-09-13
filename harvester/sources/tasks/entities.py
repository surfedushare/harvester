from collections import defaultdict
from sentry_sdk import capture_message

from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.loading import load_harvest_models
from core.constants import DeletePolicies
from core.tasks.harvest.source import harvest_source
from sources.models.harvest import HarvestEntity


@app.task(name="harvest_entities", base=DatabaseConnectionResetTask)
def harvest_entities(entity: str = None, reset: bool = False, asynchronous: bool = True) -> list[tuple[str, int]]:
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
            for set_specification in entity.set_specifications:
                state, created = HarvestState.objects.get_or_create(
                    entity=entity,
                    dataset=dataset,
                    set_specification=set_specification
                )
                datasets[dataset].append(state)

    dataset_versions = []
    for dataset, states in datasets.items():
        # Check if there are any process_result leftovers from a previous harvest process.
        # We report these occurrences, because it may indicate a problem.
        models = load_harvest_models(dataset._meta.app_label)
        logged_result_types = set()
        for process_result in models["ProcessResult"].objects.all():
            if process_result.result_type not in logged_result_types:
                capture_message(
                    f"Found unexpected process results for result type: {process_result.result_type}",
                    level="warning"
                )
                logged_result_types.add(process_result.result_type)

        # Copy data from previous harvests and delete Resources where needed.
        # After that we harvest_source to start fetching metadata.
        current_version = dataset.versions.get_current_version()
        new_version = dataset.versions.create()
        dataset_versions.append(new_version.natural_key)
        for state in states:
            if reset or not current_version or state.should_purge():
                state.clear_resources()
                state.reset(new_version)
            else:
                current_set = current_version.sets.get(name=state.set_name)
                new_version.historic_sets.add(current_set)
                state.prepare_using_set(new_version, current_set)
                if state.entity.delete_policy == DeletePolicies.NO:
                    state.clear_resources()
            if asynchronous:
                harvest_source.delay(
                    state.entity.type, state.entity.source.module, state.set_specification,
                    asynchronous=asynchronous
                )
            else:
                harvest_source(
                    state.entity.type, state.entity.source.module, state.set_specification,
                    asynchronous=asynchronous
                )

    return dataset_versions
