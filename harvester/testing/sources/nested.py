from testing.constants import SEED_DEFAULTS


def get_nested_seeds(nested_data: dict):
    for parent_seed in nested_data["results"]:
        parent_id = parent_seed["srn"]
        for nested_seed in parent_seed["simples"]:
            nested_seed["parent_id"] = parent_id
            yield nested_seed


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
    }
]
