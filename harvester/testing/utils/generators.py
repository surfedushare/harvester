from typing import Iterator
from copy import copy
from datetime import timedelta

from django.conf import settings
from django.utils.timezone import now

from datagrowth.utils import ibatch
from core.loading import load_harvest_models, load_source_configuration
from core.models.datatypes import HarvestDocument, HarvestSet


def seed_generator(source: str, size: int, sequence_properties=None, has_language: bool = False,
                   state: HarvestDocument.States = HarvestDocument.States.ACTIVE) -> list[dict]:
    sequence_properties = sequence_properties or {}
    configuration = load_source_configuration("testing", source)
    for ix in range(0, size):
        seed = copy(configuration["seed_defaults"])
        sequenced = {
            key: value.format(ix=ix) if value != "{ix}" else ix
            for key, value in sequence_properties.items()
        }
        seed.update(sequenced)
        seed["state"] = state
        if has_language:
            seed["language"] = settings.OPENSEARCH_LANGUAGE_CODES[ix % len(settings.OPENSEARCH_LANGUAGE_CODES)]
        yield seed


def document_generator(source: str, size: int, batch_size: int, set_instance: HarvestSet,
                       sequence_properties: dict = None, time_offset: dict = None,
                       state: HarvestDocument.States = HarvestDocument.States.ACTIVE) -> Iterator[HarvestDocument]:
    models = load_harvest_models("testing")
    Document = models["Document"]
    build_time = None if not time_offset else now() - timedelta(**time_offset)
    documents = [
        Document.build(seed, collection=set_instance, build_time=build_time)
        for seed in seed_generator(source, size, sequence_properties, state=state)
    ]
    for batch in ibatch(documents, batch_size=batch_size):
        Document.objects.bulk_create(batch)
        yield batch
