import os
import logging
from io import StringIO
from invoke import Context

from django.conf import settings
from django.core.management import base, call_command
from django.apps import apps
from django.db import connection

from datagrowth.utils import get_dumps_path, objects_from_disk
from system_configuration.main import create_configuration
from harvester.settings import environment
from core.loading import load_harvest_models, load_task_resources
from search.models import OpenSearchIndex
from search.tasks import index_dataset_versions


logger = logging.getLogger("harvester")


class Command(base.LabelCommand):
    """
    A command to load data from S3 bucket
    """

    metadata_models = [
        "metadata.MetadataField",
        "metadata.MetadataValue",
        "metadata.MetadataTranslation",
    ]

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('-de', '--download-edurep', action="store_true")
        parser.add_argument('-s', '--skip-download', action="store_true")
        parser.add_argument('-hs', '--harvest-source', type=str)

    def load_data(self, app_label, load_metadata=False):

        task_resources = load_task_resources(app_label)[app_label]
        resources = list(task_resources.keys()) if task_resources else []

        delete_models = resources + self.metadata_models if load_metadata else resources
        for resource_model in delete_models:
            print(f"Deleting resource {resource_model}")
            model = apps.get_model(resource_model)
            model.objects.all().delete()

        for resource_model in resources:
            print(f"Loading resource {resource_model}")
            call_command("load_resource", resource_model)

        if load_metadata:
            metadata_models = [  # for loading we need MetadataTranslations before MetadataField and MetadataValue
                self.metadata_models[2],
                *self.metadata_models[:2]
            ]
            for metadata_model in metadata_models:
                print(f"Loading metadata {metadata_model}")
                clazz = apps.get_model(metadata_model)
                load_file = os.path.join(get_dumps_path(clazz), f"{clazz.get_name()}.dump.json")
                call_command("loaddata", load_file)

    @staticmethod
    def reset_postgres_sequences(app_label):
        out = StringIO()
        call_command("sqlsequencereset", app_label, "--no-color", stdout=out)
        with connection.cursor() as cursor:
            sql = out.getvalue()
            cursor.execute(sql)

    def bulk_create_objects(self, objects):
        obj = objects[0]
        model = type(obj)
        model.objects.bulk_create(objects, ignore_conflicts=True)

    def handle_label(self, app_label, **options):

        models = load_harvest_models(app_label)

        skip_download = options["skip_download"]
        harvest_source = options.get("harvest_source", None)

        assert harvest_source or environment.service.env != "localhost", \
            "Expected a harvest source argument for a localhost environment"
        source_environment = create_configuration(harvest_source) \
            if harvest_source else environment

        # Delete old datasets
        print("Deleting old data")
        models["Document"].objects.all().delete()
        models["Dataset"].objects.all().delete()
        models["DatasetVersion"].objects.all().delete()
        if app_label == "products":
            print("Deleting old indices for products")
            OpenSearchIndex.objects.all().delete()

        if harvest_source and not skip_download:
            logger.info(f"Downloading dump files for: {app_label}")
            ctx = Context(environment)
            harvester_data_bucket = f"s3://{source_environment.aws.harvest_content_bucket}/datasets/harvester"
            ctx.run(f"aws s3 sync {harvester_data_bucket} {settings.DATAGROWTH_DATA_DIR}", echo=True)
        logger.info(f"Importing data for: {app_label}")
        for entry in os.scandir(get_dumps_path(models["Dataset"])):
            if entry.is_file():
                with open(entry.path, "r") as dump_file:
                    for objects in objects_from_disk(dump_file):
                        self.bulk_create_objects(objects)
        # Load resources
        self.load_data(app_label, app_label == "products")
        self.reset_postgres_sequences(app_label)

        # Index data
        latest_dataset_version = models["DatasetVersion"].objects.get_current_version()
        if latest_dataset_version and latest_dataset_version.index:
            latest_dataset_version.index.pushed_at = None  # forces a new push for this environment
            latest_dataset_version.index.configuration = {}  # forces recreation of configuration for environment
            latest_dataset_version.index.save()
            index_dataset_versions([latest_dataset_version.model_key], recreate_indices=True)
