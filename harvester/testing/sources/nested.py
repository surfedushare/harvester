from typing import Iterator
from core.models.datatypes import HarvestSet
from testing.constants import SEED_DEFAULTS


def get_nested_seeds(nested_data: dict) -> Iterator[dict]:
    for parent_seed in nested_data["results"]:
        if not parent_seed["simples"] and parent_seed["state"] == "deleted":
            yield {
                "parent_id": parent_seed["srn"],
                "state": parent_seed["state"]
            }
        for nested_seed in parent_seed["simples"]:
            nested_seed["parent_id"] = parent_seed["srn"]
            nested_seed["state"] = parent_seed["state"]
            yield nested_seed


def back_fill_deletes(seed: dict, harvest_set: HarvestSet) -> Iterator[dict]:
    if not seed["state"] == "deleted":
        yield seed
        return
    for doc in harvest_set.documents.filter(properties__parent_id=seed["parent_id"]):
        doc.properties["state"] = "deleted"
        yield doc.properties


OBJECTIVE = {
    key: f"$.{key}"
    for key in SEED_DEFAULTS.keys()
}
OBJECTIVE["parent_id"] = "$.parent_id"
OBJECTIVE["@"] = get_nested_seeds


SEEDING_PHASES = [
    {
        "phase": "testing",
        "strategy": "initial",
        "batch_size": 5,
        "retrieve_data": {
            "resource": "testing.MockHarvestResource",
            "method": "get",
            "args": ["nested"],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    },
    {
        "phase": "deletes",
        "strategy": "back_fill",
        "batch_size": 5,
        "contribute_data": {
            "callback": back_fill_deletes
        }
    }
]
