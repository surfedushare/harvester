from copy import copy

from django.conf import settings

from datagrowth.utils import ibatch
from core.loading import load_harvest_models, load_source_configuration


def seed_generator(source: str, size: int, sequence_properties=None, has_language: bool = False) -> list[dict]:
    sequence_properties = sequence_properties or {}
    configuration = load_source_configuration("testing", source)
    for ix in range(0, size):
        seed = copy(configuration["seed_defaults"])
        sequenced = {
            key: value.format(ix=ix) if value != "{ix}" else ix
            for key, value in sequence_properties.items()
        }
        seed.update(sequenced)
        if has_language:
            seed["language"] = settings.OPENSEARCH_LANGUAGE_CODES[ix % len(settings.OPENSEARCH_LANGUAGE_CODES)]
        yield seed


def document_generator(source: str, size: int, batch_size: int, set_instance, sequence_properties=None):
    models = load_harvest_models("testing")
    documents = [
        models["Document"].build(seed, collection=set_instance)
        for seed in seed_generator(source, size, sequence_properties)
    ]
    for batch in ibatch(documents, batch_size=batch_size):
        models["Document"].objects.bulk_create(batch)
        yield batch
