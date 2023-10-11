from operator import itemgetter

from django.utils.timezone import now

from core.loading import load_harvest_models
from core.models.datatypes import HarvestDataset, HarvestDatasetVersion, HarvestSet, HarvestDocument


def create_datatype_models(app_label: str, set_names: list[str], seeds: list[dict], docs_per_set: int) \
        -> tuple[HarvestDataset, HarvestDatasetVersion, list[HarvestSet], list[HarvestDocument]]:
    models = load_harvest_models(app_label)
    Dataset, DatasetVersion, Set, Document = itemgetter("Dataset", "DatasetVersion", "Set", "Document")(models)
    finished_at = now()
    dataset = Dataset(
        name="test",
        is_harvested=True,
        indexing=models["Dataset"].IndexingOptions.INDEX_AND_PROMOTE
    )
    dataset.clean()
    dataset.save()
    dataset_version = DatasetVersion(dataset=dataset, finished_at=finished_at, is_current=True, pending_at=None)
    dataset_version.clean()
    dataset_version.save()
    sets = []
    documents = []
    for set_name in set_names:
        harvest_set = Set(
            dataset_version=dataset_version,
            name=set_name,
            identifier="srn",
            finished_at=finished_at
        )
        harvest_set.clean()
        harvest_set.save()
        sets.append(harvest_set)
        for _ in range(0, docs_per_set):
            seed = seeds.pop()
            document = Document.build(seed, collection=harvest_set)
            document.pending_at = None
            document.finished_at = finished_at
            document.save()
            documents.append(document)
    return dataset, dataset_version, sets, documents
