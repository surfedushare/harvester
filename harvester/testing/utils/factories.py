from django.utils.timezone import now

from core.loading import load_harvest_models
from core.models.datatypes import HarvestDataset, HarvestDatasetVersion, HarvestSet, HarvestDocument


def create_datatype_models(app_label: str, set_names: list[str], seeds: list[dict], docs_per_set: int) \
        -> tuple[HarvestDataset, HarvestDatasetVersion, list[HarvestSet], list[HarvestDocument]]:
    models = load_harvest_models(app_label)
    pending_at = now()
    dataset = models["Dataset"](
        name="test",
        is_harvested=True,
        indexing=models["Dataset"].IndexingOptions.INDEX_AND_PROMOTE
    )
    dataset.clean()
    dataset.save()
    dataset_version = models["DatasetVersion"](dataset=dataset, pending_at=pending_at, is_current=True)
    dataset_version.clean()
    dataset_version.save()
    sets = []
    documents = []
    for set_name in set_names:
        harvest_set = models["Set"](
            dataset_version=dataset_version,
            name=set_name,
            identifier="srn"
        )
        harvest_set.clean()
        harvest_set.save()
        sets.append(harvest_set)
        for _ in range(0, docs_per_set):
            seed = seeds.pop()
            document = models["Document"].build(seed, collection=harvest_set)
            document.pending_at = None
            document.save()
            documents.append(document)
    return dataset, dataset_version, sets, documents
