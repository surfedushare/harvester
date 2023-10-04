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
    """
    A convenience function that loads relevant harvester models for a Django app.
    The function will work for the "core" app to provide backwards compatability.
    However the "core" loaded models may not work as expected, because they do not inherit from HarvestObject.

    :param app_label: the app model you want to load harvester models for
    :return: (dict) models
    """
    model_names = ["Dataset", "DatasetVersion", "HarvestState", "Batch", "ProcessResult"]
    if app_label == "core":
        model_names.append("Collection")
    else:
        model_names.append("Set")
    app_config = apps.get_app_config(app_label)
    models = {}
    for model_name in model_names:
        try:
            models[model_name] = apps.get_model(f"{app_label}.{model_name}")
        except LookupError:  # only here catch HarvestState which core will never have
            models[model_name] = None
    models["Document"] = apps.get_model(f"{app_label}.{app_config.document_model}")
    if "Collection" in models:
        models["Set"] = models["Collection"]
    return models


def load_source_configuration(app_label: str, source: str) -> dict[str, Any]:
    source_module = import_module(f"{app_label}.sources.{source}")
    contants_module = import_module(f"{app_label}.constants")
    return {
        "objective": source_module.OBJECTIVE,
        "seeding_phases": source_module.SEEDING_PHASES,
        "seed_defaults": contants_module.SEED_DEFAULTS
    }
