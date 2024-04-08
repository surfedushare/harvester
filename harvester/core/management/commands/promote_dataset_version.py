import logging
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.loading import load_harvest_models


logger = logging.getLogger("harvester")


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-d', '--dataset', type=str, default="")
        parser.add_argument('-hv', '--harvester-version', type=str, default=settings.VERSION)
        parser.add_argument('-i', '--dataset-version-id', type=int, default=0)
        parser.add_argument('-a', '--app-label', type=str, default="core")

    def handle(self, *args, **options):

        dataset_version_id = options["dataset_version_id"]
        dataset_name = options["dataset"]
        harvester_version = options["harvester_version"]
        app_label = options["app_label"]

        models = load_harvest_models(app_label)
        Dataset = models["Dataset"]
        DatasetVersion = models["DatasetVersion"]

        if not dataset_version_id and not dataset_name:
            raise CommandError("Dataset name required if dataset version id is not specified")

        if dataset_version_id:
            dataset_version = DatasetVersion.objects.get(pk=dataset_version_id)
        else:
            dataset = Dataset.objects.get(name=dataset_name)
            dataset_version = dataset.versions.filter(version=harvester_version).last()

        if not dataset_version:
            raise CommandError("Can't find a dataset version that matches input")

        logger.info(f"Promoting: {dataset_version.dataset.name}, {dataset_version.version} (id={dataset_version.id})")

        if getattr(dataset_version, "indices", None):
            for index in dataset_version.indices.all():
                logger.info(f"Promoting index {index.remote_name} to latest")
                index.promote_to_latest()
            dataset_version.set_current()
        elif getattr(dataset_version, "index", None):
            index = dataset_version.index
            logger.info(f"Promoting index {index.name} to latest")
            dataset_version.index.promote_all_to_latest()  # when merging languages into one index we can remove "all"
            dataset_version.set_index_promoted()
            dataset_version.set_current()
        else:
            raise CommandError("Unexpected DatasetVersion interface: neither indices nor index is available")

        logger.info("Finished promoting")
