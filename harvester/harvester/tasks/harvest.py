from django.core.management import CommandError, call_command

from core.constants import HarvestStages, Repositories
from core.logging import HarvestLogger
from core.models import Dataset, Harvest
from core.utils.harvest import prepare_harvest
from harvester.celery import app


@app.task(name="harvest")
def harvest(reset=False, no_promote=False, **kwargs):

    if not Dataset.objects.filter(is_active=True).exists():
        logger = HarvestLogger(None, "harvest_task", {})
        logger.info("Skipping legacy harvest, because there are no active legacy Datasets")
        return

    if reset:
        call_command("extend_resource_cache")

    # Iterate over all active datasets to get data updates
    for dataset in Dataset.objects.filter(is_active=True):
        # Preparing dataset state and deletes old model instances
        prepare_harvest(dataset, reset=reset)
        # First we call the commands that will query the repository interfaces
        repositories = [
            Repositories.EDUREP, Repositories.SHAREKIT, Repositories.ANATOMY_TOOL,
            Repositories.HANZE, Repositories.HAN, Repositories.HKU, Repositories.GREENI, Repositories.HVA,
            Repositories.BUAS, Repositories.EDUREP_JSONSEARCH, Repositories.PUBLINOVA, Repositories.SAXION
        ]
        for repository in repositories:
            try:
                call_command("harvest_metadata", f"--dataset={dataset.name}", f"--repository={repository}")
            except CommandError as exc:
                logger = HarvestLogger(dataset, "harvest_task", {
                    "dataset": dataset.name,
                    "repository": repository
                })
                logger.error(str(exc))

        # After getting all the metadata we'll download content
        call_command("harvest_basic_content", f"--dataset={dataset.name}", "--async")
        # We skip any video downloading/processing for now
        # Later we want YoutubeDL to download the videos and Amber to process them
        Harvest.objects.filter(stage=HarvestStages.BASIC).update(stage=HarvestStages.PREVIEW)
        # Generate the thumbnails
        call_command("generate_previews", f"--dataset={dataset.name}", "--async")
        # Based on the dataset and site we push to search engine
        index_command = ["index_dataset_version", f"--dataset={dataset.name}"]
        if no_promote or not dataset.is_latest:
            index_command += ["--no-promote"]
        if reset:
            index_command += ["--skip-evaluation"]
        call_command(*index_command)
