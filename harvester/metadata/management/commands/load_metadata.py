import os
import logging
from invoke import Context

from django.conf import settings
from django.core.management import base, call_command
from django.apps import apps

from datagrowth.utils import get_dumps_path
from system_configuration.main import create_configuration
from harvester.settings import environment


logger = logging.getLogger("harvester")


class Command(base.BaseCommand):
    """
    A command to load (only) metadata from S3 bucket.
    Consider using load_harvester_data to load all data from S3 bucket.
    """

    metadata_models = [
        "metadata.MetadataField",
        "metadata.MetadataValue",
        "metadata.MetadataTranslation",
    ]

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('-s', '--source', type=str)

    def handle(self, **options):

        # Download data
        source = options.get("source", None)
        assert source or environment.service.env != "localhost", \
            "Expected a harvest source argument for a localhost environment"
        if source != "localhost":
            source_environment = create_configuration(source) if source else environment
            logger.info("Downloading dump file for metadata")
            ctx = Context(environment)
            harvester_data_bucket = f"s3://{source_environment.aws.harvest_content_bucket}/datasets/harvester/metadata/"
            ctx.run(f"aws s3 sync {harvester_data_bucket} {settings.DATAGROWTH_DATA_DIR}/metadata", echo=True)

        logger.info("Importing metadata")
        # Delete old data
        for resource_model in self.metadata_models:
            print(f"Deleting resource {resource_model}")
            model = apps.get_model(resource_model)
            model.objects.all().delete()

        # Load new data
        metadata_models = [  # for loading we need MetadataTranslations before MetadataField and MetadataValue
            self.metadata_models[2],
            *self.metadata_models[:2]
        ]
        for metadata_model in metadata_models:
            print(f"Loading metadata {metadata_model}")
            clazz = apps.get_model(metadata_model)
            load_file = os.path.join(get_dumps_path(clazz), f"{clazz.get_name()}.dump.json")
            call_command("loaddata", load_file)
