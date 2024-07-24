from datetime import datetime, timedelta
from functools import reduce

from django.conf import settings
from django.apps import apps
from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand
from django.db.models import Q

from core.loading import load_harvest_models, load_task_resources


class Command(BaseCommand):
    """
    A convenience command to delete any data that is considered stale
    """

    def handle(self, **options):
        purge_time = make_aware(datetime.now()) - timedelta(**settings.DATA_RETENTION_PURGE_AFTER)
        task_resources = load_task_resources()
        for app_label, resources in task_resources.items():
            models = load_harvest_models(app_label)
            # Delete DatasetVersions that are not in use and overdue
            for dataset in models["Dataset"].objects.all():
                stale_dataset_versions = models["DatasetVersion"].objects.get_stale_versions(purge_time, dataset)
                for stale_dataset_version in stale_dataset_versions:
                    if app_label != "core" and stale_dataset_version.index:
                        stale_dataset_version.index.delete()
                    models["ProcessResult"].objects.filter(document__dataset_version=stale_dataset_version) \
                        ._raw_delete("default")
                    models["Document"].objects.filter(dataset_version=stale_dataset_version)._raw_delete("default")
                    stale_dataset_version.delete()
            # Now go over all resources and delete old ones without matching documents
            for resource_model, pipeline_phases in resources.items():
                model = apps.get_model(resource_model)
                for resource in model.objects.filter(purge_at__lte=purge_time):
                    document_phase_filters = [
                        Q(**{
                            f"pipeline__{pipeline_phase}__resource": resource_model.lower(),
                            f"pipeline__{pipeline_phase}__id": resource.id
                        })
                        for pipeline_phase in pipeline_phases
                    ]
                    filters = reduce(lambda x, y: x | y, document_phase_filters)
                    if not models["Document"].objects.filter(filters).exists():
                        resource.delete()
