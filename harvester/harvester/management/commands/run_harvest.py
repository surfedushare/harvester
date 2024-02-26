from time import sleep

from django.apps import apps
from django.core.management.base import BaseCommand

from core.logging import HarvestLogger
from core.models.resources.utils import extend_resource_cache
from sources.tasks import harvest_entities
from search.loading import dataset_versions_are_ready
from search.tasks import index_dataset_versions


def _load_current_dataset_versions(dataset_versions: list[tuple[str, int]]) -> list[tuple[str, int]]:
    current_versions = []
    for dataset_version_model, _ in dataset_versions:
        DatasetVersion = apps.get_model(dataset_version_model)
        current = DatasetVersion.objects.get_current_version()
        if current is None:
            app_label, model_name = dataset_version_model.split(".")
            raise ValueError(f"No fallback DatasetVersion exists for {app_label}")
        current_versions.append((dataset_version_model, current.id))
    return current_versions


class Command(BaseCommand):
    """
    A command that calls the harvest tasks.

    All harvest tasks execute in the background.
    Additional background workers spin-up together with this command when executed on AWS.
    This command remains running as long as some tasks have not yet completed to use these additional workers.
    """

    def add_arguments(self, parser):
        parser.add_argument('-r', '--reset', action="store_true",
                            help="Ignores all previous harvests and reloads all data from sources")
        parser.add_argument('-a', '--asynchronous', action="store_true")
        parser.add_argument('-rd', '--report-dataset-version', action="store_true")
        parser.add_argument('-t', '--timeout', type=int, default=60*60*8)
        parser.add_argument('-w', '--wait-interval', type=int, default=10)

    def handle(self, **options):
        reset = options["reset"]
        asynchronous = options["asynchronous"]
        report_dataset_version = options["report_dataset_version"]
        timeout = options["timeout"]
        wait_interval = options["wait_interval"]
        logger = HarvestLogger("general", "run_harvest", command_options=options, is_legacy_logger=False)

        logger.info(
            f"Running harvest command; "
            f"reset={reset}, report={report_dataset_version}, async={asynchronous}"
        )

        if reset:
            for label, resource in extend_resource_cache():
                logger.info(f"Extended cache for: {label}.{resource.get_name()}")
            logger.info("Done extending resource cache")

        dataset_versions = harvest_entities(reset=reset, asynchronous=asynchronous)
        ready = not asynchronous
        timer = 0
        while not ready and not timer >= timeout:
            ready = dataset_versions_are_ready(dataset_versions)
            sleep(wait_interval)
            timer += wait_interval
        else:
            if timer >= timeout:
                message = "Run harvest command exceeded timeout"
                logger.error(message)
                dataset_versions = _load_current_dataset_versions(dataset_versions)

        index_dataset_versions(dataset_versions)

        if report_dataset_version:
            for dataset_version_model, dataset_version_id in dataset_versions:
                DatasetVersion = apps.get_model(dataset_version_model)
                dataset_version = DatasetVersion.objects.get(id=dataset_version_id)
                logger.report_dataset_version(dataset_version)

        logger.info("Finished harvest command")
