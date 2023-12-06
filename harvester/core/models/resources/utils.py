from typing import Iterator

from django.apps import apps

from datagrowth.resources.base import Resource
from core.loading import load_task_resources


def extend_resource_cache(app_label: str = None,
                          task_resources: dict[str, dict[str, list[str]]] = None) -> Iterator[Resource]:
    task_resources = task_resources or load_task_resources(app_label=app_label)
    for label, resources in task_resources.items():
        for resource_model in resources:
            model = apps.get_model(resource_model)
            instance = model()
            instance.clean()  # this calculates the preferred purge_at datetime
            model.objects.update(purge_at=instance.purge_at)
            yield label, model
