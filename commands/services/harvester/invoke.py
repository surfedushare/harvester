import os
from invoke import task, Exit

from commands import HARVESTER_DIR
from commands.aws.ecs import run_data_engineering_task
from environments.system_configuration.main import create_configuration


def run_harvester_task(ctx, mode, command, environment=None):
    # On localhost we call the command directly and exit
    if ctx.config.service.env == "localhost":
        with ctx.cd(HARVESTER_DIR):
            ctx.run(" ".join(command), echo=True)
        return
    # For remotes we need to determine which target(s) we want to run commands for
    target_input = input(
        "Which projects do you want to run this command for (e)dusources, (p)ublinova, (m)bodata or (a)ll? "
    )
    targets = []
    match target_input:
        case "e":
            targets.append("edusources")
        case "p":
            targets.append("publinova")
        case "m":
            targets.append("mbodata")
        case "a":
            targets += ["edusources", "publinova", "mbodata"]
        case _:
            raise Exit("Aborted running harvester command, because of invalid target input", code=1)
    # On AWS we trigger a harvester task on the container cluster to run the command for us
    for target in targets:
        run_data_engineering_task(ctx, target, mode, command, environment)


@task(
    name="migrate",
    help={
        "mode": "Mode you want to migrate: development, acceptance or production. Must match APPLICATION_MODE.",
        "app_label": "The app label you want to migrate.",
        "migration": "The migration number of the app label that you want to migrate to."
    }
)
def harvester_migrate(ctx, mode, app_label=None, migration=None):
    """
    Executes migration task on container cluster for development, acceptance or production environment on AWS
    """
    if (app_label and not migration) or (not app_label and migration):
        raise Exit(
            "Specify both app_label and migration to run a specific migration or specify neither to run all migrations."
        )

    command = ["python", "manage.py", "migrate"]
    if migration:
        command += [app_label, migration]
    environment = [
        {
            "name": "DET_POSTGRES_USER",
            "value": f"{ctx.config.postgres.user}"
        },
        {
            "name": "DET_SECRETS_POSTGRES_PASSWORD",
            "value": f"{ctx.config.aws.postgres_password_arn}"
        },
    ]
    run_harvester_task(ctx, mode, command, environment)


@task(help={
    "mode": "Mode you want to load data for: localhost, development, acceptance or production. "
            "Must match APPLICATION_MODE",
    "source": "Source you want to import from: development, acceptance or production.",
    "app_label": "The Django app you want to dump data for",
})
def load_data(ctx, mode, source, app_label=None):
    """
    Loads a remote database and sets up Open Search data on localhost or an AWS cluster
    """
    if ctx.config.service.env == "production":
        raise Exit("Cowardly refusing to use production as a destination environment")

    if not app_label:
        app_labels = ["files", "products", "projects"]
    else:
        app_labels = [app_label]

    for label in app_labels:
        command = ["python", "manage.py", "load_harvester_data", label, f"--harvest-source={source}"]
        if source == "localhost":
            print(f"Will try to import app '{app_label}' using pre-downloaded files")
            command += ["--skip-download"]
        run_harvester_task(ctx, mode, command)


@task(help={
    "mode": "Mode you want to load metadata for: localhost, development, acceptance or production. "
            "Must match APPLICATION_MODE",
    "source": "Source you want to import from: development, acceptance or production."
})
def load_metadata(ctx, mode, source):
    """
    Loads the metadata models from source and loads them into Postgres.
    """
    if ctx.config.service.env == "production":
        raise Exit("Cowardly refusing to use production as a destination environment")

    command = ["python", "manage.py", "load_metadata", f"--source={source}"]

    run_harvester_task(ctx, mode, command)


@task(help={
    "mode": "Mode you want to load metadata for: localhost, development, acceptance or production. "
            "Must match APPLICATION_MODE",
    "fixture_file_path": "File path of the fixture you want to load relative to the harvester directory."
})
def load_fixture(ctx, mode, fixture_file_path):
    """
    Loads a fixture from the file system into the database.
    """
    if ctx.config.service.env == "production":
        raise Exit("Cowardly refusing to use production as a destination environment")

    file_path = os.path.join("harvester", fixture_file_path)
    if not os.path.exists(file_path):
        raise Exit(f"Fixture with file path {fixture_file_path} does not exist")

    command = ["python", "manage.py", "loaddata", fixture_file_path]

    run_harvester_task(ctx, mode, command)


@task(help={
    "mode": "Mode you want to migrate: localhost, development, acceptance or production. Must match APPLICATION_MODE",
    "reset": "Whether to reset the active datasets before harvesting",
    "asynchronous": "Whether to run harvester tasks asynchronously",
})
def harvest(ctx, mode, reset=False, asynchronous=True):
    """
    Starts a harvest tasks on the AWS container cluster or localhost
    """
    command = ["python", "manage.py", "run_harvest"]
    if reset:
        command += ["--reset"]
    if asynchronous:
        command += ["--asynchronous"]

    run_harvester_task(ctx, mode, command)


@task(name="sync_preview_media", help={
    "source": "The source you want to sync preview media from"
})
def sync_preview_media(ctx, source="production"):
    """
    Performs a sync between the preview media buckets of two environments.
    APPLICATION_MODE determines the destination environment.
    """
    if ctx.config.service.env == "production":
        raise Exit("Cowardly refusing to use production as a destination environment")

    local_directory = os.path.join("media", "harvester")
    source_config = create_configuration(source, context="host")
    source = source_config.aws.harvest_content_bucket
    source = "s3://" + source if source is not None else local_directory
    destination = ctx.config.aws.harvest_content_bucket
    destination = "s3://" + destination if destination is not None else local_directory
    profile_name = ctx.config.aws.profile_name if not ctx.config.service.env == "localhost" else \
        source_config.aws.profile_name
    for path in ["thumbnails", os.path.join("core", "previews")]:
        source_path = os.path.join(source, path)
        destination_path = os.path.join(destination, path)
        ctx.run(f"AWS_PROFILE={profile_name} aws s3 sync {source_path} {destination_path}", echo=True)


@task(help={
    "mode": "Mode you want to clean data for: localhost, development, acceptance or production. "
            "Must match APPLICATION_MODE",
    "force_user_deletes": "Whether to forcefully delete Django users marked as staff accounts"
})
def clean_data(ctx, mode, force_user_deletes=False):
    """
    Starts a clean up tasks on the AWS container cluster or localhost
    """
    command = ["python", "manage.py", "clean_data"]

    if force_user_deletes:
        command += ["--force-user-deletes"]

    run_harvester_task(ctx, mode, command)


@task(help={
    "mode": "Mode you want to push indices for: localhost, development, acceptance or production. "
            "Must match APPLICATION_MODE",
    "dataset": "Name of the dataset (a Greek letter) that you want to promote to latest index "
               "(ignored if version_id is specified)",
    "version": "Version of the harvester that created the dataset version you want to index "
               "Defaults to latest version (ignored if version_id is specified)",
    "version_id": "Id of the DatasetVersion you want to promote"
})
def promote_dataset_version(ctx, mode, dataset=None, version=None, version_id=None):
    """
    Starts a task on the AWS container cluster or localhost to promote a DatasetVersion index to latest
    """
    command = ["python", "manage.py", "promote_dataset_version", ]
    if version_id:
        command += [f"--dataset-version-id={version_id}"]
    elif dataset:
        command += [f"--dataset={dataset}"]
        if version:
            command += [f"--harvester-version={version}"]
    else:
        Exit("Either specify a dataset of a dataset version id")
    run_harvester_task(ctx, mode, command)


@task(help={
    "mode": "Mode you want to dump data for: localhost, development, acceptance or production. "
            "Must match APPLICATION_MODE",
    "app_label": "Name of the app_label that you want to dump data for."
})
def dump_data(ctx, mode, app_label=None):
    """
    Starts a task on the AWS container cluster to dump a specific Django app and its models
    """
    if not app_label:
        app_labels = ["files", "products", "projects"]
    else:
        app_labels = [app_label]

    for label in app_labels:
        print(f"Start dumping data for: {label}")
        command = ["python", "manage.py", "dump_harvester_data", label]
        run_harvester_task(ctx, mode, command)


@task()
def sync_harvest_content(ctx, source, path="core"):
    """
    Performs a sync between the harvest content buckets of two environments
    """
    local_directory = os.path.join("media", "harvester")
    source_config = create_configuration(source, context="host")
    source = source_config.aws.harvest_content_bucket
    if source is None:
        source = local_directory
    else:
        source = "s3://" + source
    destination = ctx.config.aws.harvest_content_bucket
    if destination is None:
        destination = local_directory
    else:
        destination = "s3://" + destination
    source_path = os.path.join(source, path)
    destination_path = os.path.join(destination, path)
    ctx.run(f"aws s3 sync {source_path} {destination_path}", echo=True)


@task(help={
    "mode": "Mode you want to sync metadata for: localhost, development, acceptance or production. "
            "Must match APPLICATION_MODE"
})
def sync_metadata(ctx, mode):
    """
    Starts a task on the AWS container cluster or localhost to sync metadata instances with Open Search data.
    """
    command = ["python", "manage.py", "sync_metadata"]

    run_harvester_task(ctx, mode, command)
