from typing import Type

from datagrowth.resources import HttpResource


def build_seeding_phases(resource: Type[HttpResource], objective: dict) -> list[dict]:
    resource_label = f"{resource._meta.app_label}.{resource._meta.model_name}"
    return [
        {
            "phase": "research_outputs",
            "strategy": "initial",
            "batch_size": 100,
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
