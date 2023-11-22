from testing.constants import SEED_DEFAULTS


OBJECTIVE = {
    key: f"$.{key}"
    for key in SEED_DEFAULTS.keys()
}
OBJECTIVE["@"] = "$.results"


SEEDING_PHASES = [
    {
        "phase": "testing",
        "strategy": "initial",
        "batch_size": 5,
        "retrieve_data": {
            "resource": "testing.MockHarvestResource",
            "method": "get",
            "args": ["simple"],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
