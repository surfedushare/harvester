from celery.result import GroupResult, AsyncResult
from celery import states


def monitor_tasks(task_ids: list[str]) -> dict[str, bool | list[str]]:
    """
    Check if all indexing tasks are complete.
    Notice that this may often call Redis so care should be taken with group sizes.
    """

    all_complete = True
    failed_tasks = []

    for task_id in task_ids:
        # Try to restore as a GroupResult
        group_result = GroupResult.restore(task_id)

        if group_result is not None:
            # Check if all tasks in group are ready
            if not group_result.ready():
                all_complete = False

            # Check for failures
            for task in group_result.results:
                if task.state == states.FAILURE:
                    failed_tasks.append(f"Task {task.id} failed: {task.result}")

                # For chords, check the callback
                if hasattr(task, 'parent') and task.parent:
                    callback = task.parent
                    if not callback.ready():
                        all_complete = False
                    if callback.state == states.FAILURE:
                        failed_tasks.append(f"Callback {callback.id} failed: {callback.result}")
        else:
            # Try as a regular AsyncResult
            result = AsyncResult(task_id)
            if not result.ready():
                all_complete = False
            if result.state == states.FAILURE:
                failed_tasks.append(f"Task {result.id} failed: {result.result}")

    return {
        "all_complete": all_complete,
        "failed_tasks": failed_tasks
    }
