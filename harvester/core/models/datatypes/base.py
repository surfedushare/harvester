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
    pending_at = models.DateTimeField(default=now, null=True, blank=True)

    def reset_task_results(self) -> None:
        self.pipeline = {}
        self.tasks = self._meta.get_field("tasks").default()
        self.derivatives = {}
        self.pending_at = None
        self.clean()
        self.save()

    def get_pending_tasks(self) -> list[str]:
        pending_tasks = []
        for task_name, conditions in self.tasks.items():
            is_pending_task = False
            for check in conditions["checks"]:
                negate = check.startswith("!")
                check_attribute = getattr(self, check if not negate else check[1:])
                if not check_attribute and not negate or check_attribute and negate:
                    break
            else:
                is_pending_task = True
            is_success = self.pipeline.get(task_name, {}).get("success", False)
            if is_pending_task and not is_success:
                pending_tasks.append(task_name)
        return pending_tasks

    class Meta:
        abstract = True
