import os
import logging
from invoke import Context

from django.apps import apps
from django.conf import settings
from django.core.management import base, call_command
from datagrowth.utils import get_dumps_path, object_to_disk, queryset_to_disk

from harvester.settings import environment
from core.loading import load_harvest_models, load_task_resources


logger = logging.getLogger("harvester")


class Command(base.LabelCommand):

    resources = [
        "core.HttpTikaResource",
        "core.ExtructResource",
        "core.YoutubeThumbnailResource",
        "core.PdfThumbnailResource",
        "sharekit.SharekitMetadataHarvest",
        "edurep.EdurepOAIPMH"
    ]

    metadata = [
        "metadata.MetadataField",
        "metadata.MetadataTranslation",
        "metadata.MetadataValue",
    ]

    def dump_resources(self, app_label):
        if app_label == "core":
            resources = self.resources
        else:
            resources = load_task_resources(app_label)[app_label]
        paths = []
        for resource_model in resources:
            clazz = apps.get_model(resource_model)
            dump_file = os.path.join(get_dumps_path(clazz), f"{clazz.get_name()}.dump.json")
            paths.append(dump_file)
            print(f"Dumping {clazz.get_name()} to {dump_file}")
            call_command("dump_resource", resource_model)
        return paths

    def dump_metadata(self):
        paths = []
        for metadata_model in self.metadata:
            clazz = apps.get_model(metadata_model)
            dump_path = get_dumps_path(clazz)
            dump_file = os.path.join(dump_path, f"{clazz.get_name()}.dump.json")
            if not os.path.exists(dump_path):
                os.makedirs(dump_path)
            paths.append(dump_file)
            print(f"Dumping {clazz.get_name()} to {dump_file}")
            call_command("dumpdata", metadata_model, output=dump_file)
        return paths

    def handle_label(self, app_label, **options):
        models = load_harvest_models(app_label)
        dataset_files = []

        for dataset in models["Dataset"].objects.all():
            destination = get_dumps_path(dataset)
            if not os.path.exists(destination):
                os.makedirs(destination)
            dataset_file = os.path.join(destination, f"{dataset.name}.{dataset.id}.json")
            with open(dataset_file, "w") as json_file:
                object_to_disk(dataset, json_file)
                if app_label == "core":
                    queryset_to_disk(dataset.harvestsource_set, json_file)
                    queryset_to_disk(dataset.harvest_set, json_file)
                else:
                    for version in dataset.versions.filter(is_current=True):
                        if version.index:
                            object_to_disk(version.index, json_file)
                queryset_to_disk(dataset.versions.filter(is_current=True), json_file)
                for version in dataset.versions.filter(is_current=True):
                    if app_label == "core":
                        queryset_to_disk(version.indices, json_file)
                    queryset_to_disk(version.sets.all(), json_file)
                    queryset_to_disk(version.documents.all(), json_file)
            dataset_files.append(dataset_file)

        resource_files = self.dump_resources(app_label)
        metadata_files = self.dump_metadata() if app_label in ["core", "products"] else []

        # Sync files with AWS
        if environment.service.env != "localhost":
            logger.info("Uploading files to AWS")
            ctx = Context(environment)
            harvester_data_bucket = f"s3://{environment.aws.harvest_content_bucket}/datasets/harvester"
            for file in dataset_files + resource_files + metadata_files:
                remote_file = harvester_data_bucket + file.replace(settings.DATAGROWTH_DATA_DIR, "", 1)
                ctx.run(f"aws s3 cp {file} {remote_file}", echo=True)
