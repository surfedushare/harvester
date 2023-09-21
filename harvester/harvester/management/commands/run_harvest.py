import logging
from time import sleep

from django.core.management.base import BaseCommand

from sources.tasks import harvest_entities
from search.loading import dataset_versions_are_ready
from search.tasks import index_dataset_versions


logger = logging.getLogger("harvester")


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

    def handle(self, **options):
        reset = options["reset"]
        asynchronous = options["asynchronous"]
        report_dataset_version = options["report_dataset_version"]

        logger.info(
            f"Running harvest command; "
            f"reset={reset}, report={report_dataset_version}, async={asynchronous}"
        )

        dataset_versions = harvest_entities(reset=reset, asynchronous=asynchronous)
        ready = not asynchronous
        while not ready:
            ready = dataset_versions_are_ready(dataset_versions)
            sleep(10)
        index_dataset_versions(dataset_versions)
