from invoke import Collection
from environments.data_engineering.configuration import create_configuration_and_session
from commands.postgres.fabric import setup_postgres_remote
from commands.services.harvester.fabric import connect_with_shell


harvester_collection = Collection("hrv", setup_postgres_remote, connect_with_shell)


harvester_environment, _ = create_configuration_and_session()
namespace = Collection(
    harvester_collection
)
namespace.configure(harvester_environment)
