from django.db import models
from django.utils.timezone import now


class HarvestObjectMixin(models.Model):

    pipeline = models.JSONField(default=dict, blank=True)
    tasks = models.JSONField(default=dict, blank=True)
    derivatives = models.JSONField(default=dict, blank=True)
    pending_at = models.DateTimeField(default=now, null=True, blank=True)

    def get_pending_tasks(self) -> list[str]:
        pending_tasks = []
        for task_name, conditions in self.tasks.items():
            # If a task has already run it can't be pending to prevent eternal loops
            has_run = self.pipeline.get(task_name, False)
            # Check attributes on the object to see if this task is pending
            is_pending_task = False
            for check in conditions["checks"]:
                negate = check.startswith("!")
                check_attribute = getattr(self, check if not negate else check[1:])
                if not check_attribute and not negate or check_attribute and negate:
                    break
            else:
                is_pending_task = True
            # Check if dependencies for the task are met
            has_met_dependencies = True
            for dependency in conditions["depends_on"]:
                # Dependencies based on content we skip in this abstract method (where content is not always available)
                if dependency.startswith("$"):
                    continue
                # Dependencies based on other tasks are checked through the pipeline attribute
                if not self.pipeline.get(dependency, {}).get("success"):
                    has_met_dependencies = False
                    break
            # Only if all conditions are satisfied we consider the task pending
            if not has_run and is_pending_task and has_met_dependencies:
                pending_tasks.append(task_name)
        return pending_tasks

    class Meta:
        abstract = True
