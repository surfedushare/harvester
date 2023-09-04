from django.db.transaction import atomic
from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.loading import load_harvest_models


@app.task(name="testing_after_dataset_version", base=DatabaseConnectionResetTask)
@atomic
def testing_after_dataset_version(app_label, dataset_version_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    DatasetVersion = models["DatasetVersion"]
    for dataset_version in DatasetVersion.objects.filter(id__in=dataset_version_ids).select_for_update():
        dataset_version.pipeline["testing_after_dataset_version"] = {
            "success": True
        }
        dataset_version.save()
