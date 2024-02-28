from typing import Type

from datagrowth.resources import HttpResource


HBO_KENNISBANK_SET_TO_PROVIDER = {
    "greeni:PUBVHL": {
        "ror": None,
        "external_id": None,
        "slug": "PUBVHL",
        "name": "Hogeschool Van Hall Larenstein"
    },
    "saxion:kenniscentra": {
        "ror": None,
        "external_id": None,
        "slug": "saxion",
        "name": "Saxion"
    }
}


def build_seeding_phases(resource: Type[HttpResource], objective: dict) -> list[dict]:
    resource_label = f"{resource._meta.app_label}.{resource._meta.model_name}"
    return [
        {
            "phase": "records",
            "strategy": "initial",
            "batch_size": 25,
            "retrieve_data": {
                "resource": resource_label,
                "method": "get",
                "args": [],
                "kwargs": {},
            },
            "contribute_data": {
                "objective": objective
            }
        }
    ]
