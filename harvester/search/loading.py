from typing import Type

from django.apps import apps

from core.models.datatypes.dataset import HarvestDataset, HarvestDatasetVersion


def load_data_models(dataset_version_model, dataset_version_id) \
        -> tuple[Type[HarvestDataset], Type[HarvestDatasetVersion], HarvestDatasetVersion]:
    dataset_version_model = dataset_version_model.lower()
    DatasetVersion = apps.get_model(dataset_version_model)
    Dataset = apps.get_model(dataset_version_model.replace("datasetversion", "dataset"))
    dataset_version = DatasetVersion.objects.select_related("dataset").filter(id=dataset_version_id).last()
    return Dataset, DatasetVersion, dataset_version


def dataset_versions_are_ready(dataset_versions: list[tuple[str, id]]) -> bool:
    for dataset_version_model, dataset_version_id in dataset_versions:
        Dataset, DatasetVersion, dataset_version = load_data_models(dataset_version_model, dataset_version_id)
        if dataset_version is None:
            return False
        elif not dataset_version.is_current:
            return False
    return True
