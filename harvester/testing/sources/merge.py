from testing.constants import SEED_DEFAULTS


OBJECTIVE = {
    key: f"$.{key}"
    for key in SEED_DEFAULTS.keys()
}
OBJECTIVE["@"] = "$"


SEEDING_PHASES = [
    {
        "phase": "ids",
        "strategy": "initial",
        "batch_size": 5,
        "retrieve_data": {
            "resource": "testing.MockHarvestResource",
            "method": "get",
            "args": ["merge"],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": {
                "@": "$",
                "external_id": "$.id"
            }
        }
    },
    {
        "phase": "details",
        "strategy": "merge",
        "batch_size": None,
        "retrieve_data": {
            "resource": "testing.MockDetailResource",
            "method": "get",
            "args": [
                "#.args.0",  # will resolve to the first argument of the call to the processor
                "$.external_id"
            ],
            "kwargs": {},
        },
        "contribute_data": {
            "merge_on": "external_id",
            "objective": OBJECTIVE
        }
    }
]
