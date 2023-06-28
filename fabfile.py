from invoke import Collection
from environments.system_configuration.main import create_configuration_and_session
from commands.utils import assert_repo_root_directory
from commands.postgres.fabric import setup_postgres_remote
from commands.services.harvester.fabric import connect_with_shell


assert_repo_root_directory()


harvester_collection = Collection("hrv", connect_with_shell)
database_collection = Collection("db", setup_postgres_remote)


harvester_environment, _ = create_configuration_and_session()
namespace = Collection(
    harvester_collection,
    database_collection
)
namespace.configure(harvester_environment)
