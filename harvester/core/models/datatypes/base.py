from django.db import models
from django.utils.timezone import now


def simple_metadata_default() -> dict:
    return {
        "created_at": None,
        "modified_at": None,
        "deleted_at": None
    }


class HarvestObjectMixin(models.Model):

    metadata = models.JSONField(default=simple_metadata_default, blank=True)
    pipeline = models.JSONField(default=dict, blank=True)
    tasks = models.JSONField(default=dict, blank=True)
    derivatives = models.JSONField(default=dict, blank=True)
    pending_at = models.DateTimeField(default=now)

    def get_pending_tasks(self) -> list[str]:
        pending_tasks = []
        for task_name, conditions in self.tasks.items():
            is_pass_checks = all(
                getattr(self, check)
                for check in conditions["checks"]
            )
            has_run = task_name in self.pipeline
            if is_pass_checks and not has_run:
                pending_tasks.append(task_name)
        return pending_tasks

    class Meta:
        abstract = True
