from typing import Type
from collections import defaultdict

from django.utils.timezone import now
from celery import signature, chord
from celery.canvas import Signature  # for type checking only

from core.models.datatypes.base import HarvestObjectMixin as HarvestObject


class PendingHarvestObjects(Exception):
    pass


class PendingHarvestDocuments(PendingHarvestObjects):
    pass


class PendingHarvestSets(PendingHarvestObjects):
    pass


def load_pending_harvest_instances(*args, model: Type[HarvestObject] = None,
                                   as_list: bool = False) -> list[HarvestObject] | HarvestObject:
    if not args:
        raise ValueError("load_pending_harvest_instances expects at least one model id or model instance")
    # We check that we didn't get already loaded instances and return them if we do
    if isinstance(args[0], model):
        if len(args) == 1 and not as_list:
            return args[0] if args[0].pending_at else None
        return [instance for instance in args if instance.is_pending]
    # When getting ids we load them from the database
    if len(args) == 1 and not as_list:
        return model.objects.filter(id=args[0], pending_at__isnull=False).first()
    return list(model.objects.filter(id__in=args, pending_at__isnull=False))


def validate_pending_harvest_instances(instances: list[HarvestObject] | HarvestObject,
                                       model: Type[HarvestObject]) -> list[HarvestObject]:
    if instances is None:
        return []
    instances = instances if isinstance(instances, list) else [instances]
    finished = []
    pending = []
    for instance in instances:
        # We skip any containers that have pending content
        if hasattr(instance, "documents") and instance.documents.filter(pending_at__isnull=False).exists():
            raise PendingHarvestDocuments()
        elif hasattr(instance, "collections") and instance.collections.filter(pending_at__isnull=False).exists():
            raise PendingHarvestSets()
        # Then we check if the instance is done or is pending
        elif not instance.get_pending_tasks():
            finished.append(instance)
            instance.pending_at = None
            instance.finished_at = now()
        else:
            pending.append(instance)
    model.objects.bulk_update(finished, ["pending_at", "finished_at"])
    return pending


def dispatch_harvest_object_tasks(app_label: str, *args, callback=Signature, asynchronous=True) -> Signature | None:
    pending_tasks = defaultdict(list)
    for obj in args:
        for pending_task in obj.get_pending_tasks():
            pending_tasks[pending_task].append(obj.id)
    if not pending_tasks:
        return
    task_signatures = [signature(task_name, args=(app_label, obj_ids,)) for task_name, obj_ids in pending_tasks.items()]
    if asynchronous:
        return chord(task_signatures)(callback)
    for task in task_signatures:
        task()
    callback()
