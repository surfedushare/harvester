from datetime import datetime

from django.apps import apps
from django.core.management.base import LabelCommand, CommandError

from core.loading import load_harvest_models
from core.models.datatypes.dataset import HarvestDataset
from search.tasks import index_dataset_versions


class Command(LabelCommand):

    def handle_label(self, label, **options):
        try:
            app_config = apps.get_app_config(label)
        except LookupError:
            raise CommandError(f"App {label} not found")

        storages = load_harvest_models(app_config.label)
        current_version = storages.DatasetVersion.objects.get_current_version()
        if current_version is None:
            raise CommandError(f"No current DatasetVersion found for {label}")

        if current_version.dataset.indexing is HarvestDataset.IndexingOptions.NO:
            raise CommandError(f"Dataset for {label} does not support indexing")

        index_dataset_versions(
            [(f"{app_config.label}.DatasetVersion", current_version.id)],
            recreate_indices=True, index_since=datetime(year=1970, month=1, day=1), asynchronous=False
        )
