from copy import copy

from core.tasks.harvest.base import load_source_configuration


def seed_generator(entity: str, size: int, sequence_properties=None) -> list[dict]:
    sequence_properties = sequence_properties or {}
    configuration = load_source_configuration("testing", entity)
    for ix in range(0, size):
        seed = copy(configuration["seed_defaults"])
        sequenced = {
            key: value.format(ix=ix) if value != "{ix}" else ix
            for key, value in sequence_properties.items()
        }
        seed.update(sequenced)
        yield seed
