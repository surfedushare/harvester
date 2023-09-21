from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.models.datatypes.base import HarvestObjectMixin as HarvestObject
    from core.models.datatypes.dataset import HarvestDataset
    from core.models.harvest import HarvestState

from typing import Any
from importlib import import_module

from django.apps import apps


def load_harvest_models(app_label: str) -> dict[str, HarvestObject | HarvestDataset | HarvestState]:
    models = ["Dataset", "DatasetVersion", "Set", "HarvestState", "Batch", "ProcessResult"]
    app_config = apps.get_app_config(app_label)
    models = {
        model_name: apps.get_model(f"{app_label}.{model_name}")
        for model_name in models
    }
    models["Document"] = apps.get_model(f"{app_label}.{app_config.document_model}")
    return models


def load_source_configuration(app_label: str, source: str) -> dict[str, Any]:
    source_module = import_module(f"{app_label}.sources.{source}")
    contants_module = import_module(f"{app_label}.constants")
    return {
        "objective": source_module.OBJECTIVE,
        "seeding_phases": source_module.SEEDING_PHASES,
        "seed_defaults": contants_module.SEED_DEFAULTS
    }
