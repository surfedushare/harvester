from __future__ import annotations
from typing import TYPE_CHECKING, Type
if TYPE_CHECKING:
    from core.models.datatypes.dataset import HarvestDataset
    from core.models.datatypes.set import HarvestSet
    from core.models.harvest import HarvestState as HarvestStateType
    from core.models.pipeline import BatchBase, ProcessResultBase
    from core.models.datatypes.overwrite import HarvestOverwrite

from typing import Any
from importlib import import_module
from collections import defaultdict

from django.apps import apps
from datagrowth.datatypes.types import DataStorages


class HarvesterDataStorages(DataStorages):
    """
    Extended DataStorages class that includes additional harvester-specific models.
    """

    Set: Type[HarvestSet] = None
    Dataset: Type[HarvestDataset] = None
    HarvestState: Type[HarvestStateType] = None
    Batch: Type[BatchBase] = None
    ProcessResult: Type[ProcessResultBase] = None
    Overwrite: Type[HarvestOverwrite] | None = None

    @classmethod
    def from_label(cls, label: str) -> HarvesterDataStorages:
        """
        Create a HarvesterDataStorages instance from an app label.

        :param label: The app label to load models from
        :return: A HarvesterDataStorages instance with all models loaded
        """
        # First create base DataStorages instance
        storages = super().from_label(label)
        app_label = label.split(".")[0]

        # Create HarvesterDataStorages instance with base models
        harvester_storages = cls(
            model=storages.model,
            DatasetVersion=storages.DatasetVersion,
            Collection=storages.Collection,
            Document=storages.Document
        )

        # Load required models - these will raise LookupError if missing
        harvester_storages.Set = harvester_storages.Collection
        harvester_storages.Dataset = apps.get_model(f"{app_label}.Dataset")
        harvester_storages.HarvestState = apps.get_model(f"{app_label}.HarvestState")
        harvester_storages.Batch = apps.get_model(f"{app_label}.Batch")
        harvester_storages.ProcessResult = apps.get_model(f"{app_label}.ProcessResult")

        # Load optional Overwrite model
        try:
            harvester_storages.Overwrite = apps.get_model(f"{app_label}.Overwrite")
        except LookupError:
            harvester_storages.Overwrite = None

        return harvester_storages


def load_harvest_models(app_label: str) -> HarvesterDataStorages:
    """
    A convenience function that loads relevant harvester models for a Django app using DataStorages.

    :param app_label: the app model you want to load harvester models for
    :return: A HarvesterDataStorages instance with all models loaded
    """
    app_config = apps.get_app_config(app_label=app_label)
    return HarvesterDataStorages.from_label(f"{app_label}.{app_config.document_model}")


def load_source_configuration(app_label: str, source: str) -> dict[str, Any]:
    source_module = import_module(f"{app_label}.sources.{source}")
    contants_module = import_module(f"{app_label}.constants")
    return {
        "objective": source_module.OBJECTIVE,
        "seeding_phases": source_module.SEEDING_PHASES,
        "webhook_data_transformer": getattr(source_module, "WEBHOOK_DATA_TRANSFORMER", None),
        "seed_defaults": contants_module.SEED_DEFAULTS,
    }


def load_task_resources(app_label: str = None,
                        extra_resources: dict[str, dict[str, list[str]]] = None) -> dict[str: dict[str: list[str]]]:
    assert app_label is None or app_label != "core", \
        "Can't load task resources for core, because its classes are abstract"

    if app_label is None:
        app_configs = [
            config for config in apps.get_app_configs()
            if hasattr(config, "document_model") and config.label not in ["core", "testing"]
        ]
    else:
        app_configs = [apps.get_app_config(app_label)]

    task_resources = {}
    for config in app_configs:
        storages = load_harvest_models(config.label)
        task_resources[config.label] = defaultdict(list)

        # Check models that have tasks
        for model in [storages.DatasetVersion, storages.Collection, storages.Document]:
            model_task_definitions = model._meta.get_field("tasks").default()
            for task_name, task_definition in model_task_definitions.items():
                for resource in task_definition["resources"]:
                    task_resources[config.label][resource].append(task_name)

    if extra_resources:
        task_resources.update(extra_resources)
    return task_resources
