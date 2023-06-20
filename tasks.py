from invoke import Collection

from environments.data_engineering.configuration import create_configuration_and_session
from commands.postgres.invoke import setup_postgres_localhost
from commands.opensearch.tasks import create_decompound_dictionary, push_decompound_dictionary, push_indices_template
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
                                  create_decompound_dictionary, push_decompound_dictionary, generate_previews,
                                  extend_resource_cache, sync_preview_media, sync_metadata, push_indices_template,
                                  harvester_migrate, load_metadata)
container_collection = Collection("container", build, push, promote, deploy)
aws_collection = Collection("aws", print_available_images, sync_repository_state, cleanup_ecs_artifacts,
                            publish_tika_image)


harvester_environment, _ = create_configuration_and_session()
namespace = Collection(
    harvester_collection,
    aws_collection,
    prepare_builds,
    test_collection,
)
namespace.configure(harvester_environment)
