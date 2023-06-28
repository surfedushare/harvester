from invoke import Collection

from environments.system_configuration.main import create_configuration_and_session
from commands.postgres.invoke import setup_postgres_localhost
from commands.opensearch.tasks import search_collection
from commands.aws.ecs import cleanup_ecs_artifacts
from commands.aws.repository import sync_repository_state
from commands.deploy import prepare_builds, build, push, deploy, promote, print_available_images, publish_tika_image
from commands.test import test_collection
from commands.services.harvester.invoke import (load_data, harvest, clean_data, index_dataset_version,
                                                dump_data, sync_harvest_content, generate_previews,
                                                promote_dataset_version, extend_resource_cache, sync_preview_media,
                                                sync_metadata, harvester_migrate, load_metadata)


harvester_collection = Collection("hrv", setup_postgres_localhost, harvest, clean_data, load_data,
                                  index_dataset_version, dump_data, sync_harvest_content, promote_dataset_version,
                                  generate_previews, extend_resource_cache, sync_preview_media, sync_metadata,
                                  load_metadata)
database_collection = Collection("db", setup_postgres_localhost, harvester_migrate)
container_collection = Collection("container", build, push, promote, deploy, prepare_builds)
aws_collection = Collection("aws", print_available_images, sync_repository_state, cleanup_ecs_artifacts,
                            publish_tika_image)


harvester_environment, _ = create_configuration_and_session()
namespace = Collection(
    harvester_collection,
    container_collection,
    aws_collection,
    database_collection,
    search_collection,
    test_collection,
)
namespace.configure(harvester_environment)
