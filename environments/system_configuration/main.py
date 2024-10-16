"""
This module exposes utilities to handle environment specific configuration.
The idea is that configuration is managed by just three environment variables:
 * APPLICATION_MODE (exposed as MODE)
 * APPLICATION_CONTEXT (exposed as CONTEXT)
 * APPLICATION_PROJECT (exposed as PROJECT)
The first specifies a mode like "production", "acceptance" or "development".
The second specifies where the code is run either "host" or "container"
The third indicates which project specific configuration to load.

Any configuration that you want to override can be set by using environment variables prefixed with "DET_".
For instance: if you want to override the django.debug configuration set DET_DJANGO_DEBUG=0.
If you leave empty any DET environment variables they are assumed to be unset. Use "0" for a False value.

Parts of the configuration is identical across environments
except for the environment prefix like "dev", "acc" and "prod" or the Amazon account id.
For these configurations the aws.py file in this file holds configuration templates,
that can be filled out with the prefix or account id.
All secrets are configuration templates that need an account id,
but these secret ARN's get swapped for their secret values as well.
"""
import os
import json
from invoke.config import Config
import boto3
import requests

from .aws import (AWS_ENVIRONMENT_CONFIGURATIONS, AWS_ACCOUNT_CONFIGURATIONS, AWS_SECRET_CONFIGURATIONS,
                  ENVIRONMENT_NAMES_TO_CODES, ENVIRONMENT_NAMES_TO_ACCOUNT_IDS)


ENVIRONMENTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODE = os.environ.get("APPLICATION_MODE", "production")
CONTEXT = os.environ.get("APPLICATION_CONTEXT", "container")
PROJECT = os.environ.get("APPLICATION_PROJECT", "edusources")
TEAM = os.environ.get("APPLICATION_TEAM", "web")
ECS_CONTAINER_METADATA_URI = os.environ.get("ECS_CONTAINER_METADATA_URI", None)

PREFIX = "DET"


# Now we'll delete any items that are DET variables, but with empty values
# Use a value of "0" for a Boolean instead of an empty string
invalid_keys = []
for key, value in os.environ.items():
    if key.startswith(f"{PREFIX}_") and value == "":
        invalid_keys.append(key)
for key in invalid_keys:
    os.environ.pop(key)


# Using a custom configuration class
class DETConfig(Config):
    env_prefix = PREFIX

    def load_project(self, merge=True):
        self._load_file(prefix="project", absolute=True, merge=merge)

    def merge(self):
        super().merge()
        self.render_configuration_templates()

    def render_configuration_templates(self):
        def _render(configuration):
            if isinstance(configuration, dict):
                for key, value in configuration.items():
                    configuration[key] = _render(value)
            if not isinstance(configuration, str):
                return configuration
            for replacement in ["account", "environment_code"]:
                if f"{{{replacement}}}" in configuration:
                    value = getattr(self.aws, replacement)
                    configuration = configuration.format(**{replacement: value})
                    return configuration
            return configuration
        for key, value in self._config.items():
            self._config[key] = _render(value)


def build_configuration_defaults(environment):
    environment_code = ENVIRONMENT_NAMES_TO_CODES[environment]
    account_id = ENVIRONMENT_NAMES_TO_ACCOUNT_IDS[environment]
    # Computing and updating various default values including configuration template strings
    defaults = DETConfig.global_defaults()
    defaults.update({
        "project": {
            "name": PROJECT
        },
        "service": {
            "env": environment,
            "name": "harvester",
            "directory": "harvester",
            "deploy": {
                "tags": {
                    "central": f"{environment_code}-central",
                    "edusources": f"{environment_code}-edusources",
                    "mbodata": f"{environment_code}-mbodata",
                    "publinova": f"{environment_code}-publinova",
                }
            }
        },
        "aws": {
            "account": account_id,
            "environment_code": environment_code,
            "cluster_name": "data-engineering",
            "production": {
                "account": "017973353230",
                "profile_name": "pol-prod",
                "registry": "017973353230.dkr.ecr.eu-central-1.amazonaws.com"
            },
            "repositories": ["harvester", "harvester-nginx"],
            "task_definition_families": [
                "web", "celery", "central",
                "command-edusources", "command-publinova", "command-mbodata"
            ]
        },
        "secrets": dict()
    })
    defaults["aws"].update(**AWS_ENVIRONMENT_CONFIGURATIONS)
    defaults["aws"].update(**AWS_ACCOUNT_CONFIGURATIONS)
    defaults["secrets"].update(**AWS_SECRET_CONFIGURATIONS)
    # We'll fetch the container metadata.
    # For more background on ECS_CONTAINER_METADATA_URI read:
    # https://docs.aws.amazon.com/AmazonECS/latest/userguide/task-metadata-endpoint-v3-fargate.html
    container_metadata = {}
    if ECS_CONTAINER_METADATA_URI:
        response = requests.get(ECS_CONTAINER_METADATA_URI)
        if response.status_code == 200:
            container_metadata = response.json()
    # Adding container specific information as configuration for reference in the application
    defaults.update({
        "container": {
            "id": container_metadata.get("DockerId", None),
            "family": container_metadata.get("family", None)
        }
    })
    # Returning results
    return defaults


def create_configuration(mode=None, context="container"):
    """
    We're using invoke Config as base for our configuration:
    http://docs.pyinvoke.org/en/stable/concepts/configuration.html#config-hierarchy.
    Since the config is created outside of invoke it works slightly different than normal.
    First we load configuration templates from aws.py through user configuration and build_container_overrides.
    The system invoke files are the common configuration files.
    The project invoke file contains configuration specific to "edusources" or "publinova".
    Runtime configurations are used to load superuser configurations and are set only in a host context.
    Shell environment variables override all other configuration.

    :param mode: the mode you want a configuration for
    :param context: the context you want a configuration for (host or container)
    :return: invoke configuration
    """
    mode = mode or MODE
    configuration_directory = os.path.join(ENVIRONMENTS)
    config = DETConfig(
        defaults=build_configuration_defaults(mode),
        system_prefix=os.path.join(configuration_directory, mode) + os.path.sep,
        lazy=True
    )
    config._project_path = os.path.join(configuration_directory, f"{PROJECT}.yml")
    if context == "host":
        config.set_runtime_path(os.path.join(configuration_directory, mode, "superuser.invoke.yml"))
    config.load_system()
    config.load_user()
    config.load_project()
    config.load_runtime()
    config.load_shell_env()
    config.render_configuration_templates()
    return config


def create_configuration_and_session(mode=None, context=None):
    """
    Creates an environment holding all the configuration for current mode and creates an AWS session.
    The used profile for AWS session is either default or the configured profile_name for the environment

    :param mode: the mode you want a configuration for
    :param context: the context you want a configuration for (host or container)
    :return: environment, session
    """
    mode = mode or MODE
    context = context or CONTEXT

    # Now we use the customize invoke load as described above
    environment = create_configuration(mode, context=context)
    # Creating a AWS session based on configuration and context
    session = boto3.Session() if context != "host" else boto3.Session(profile_name=environment.aws.profile_name)

    # Load secrets (we resolve secrets during runtime so that AWS can manage them)
    if environment.aws.load_secrets and context != "unprivileged":
        secrets_manager = session.client('secretsmanager')
        # This skips over any non-AWS secrets
        secrets = environment.secrets or {}
        aws_secrets = []
        for group_name, group_secrets in secrets.items():
            for secret_name, secret_id in group_secrets.items():
                if secret_id is not None and secret_id.startswith("arn:aws:secretsmanager"):
                    aws_secrets.append((group_name, secret_name, secret_id,))
        # Here we found AWS secrets which we load using boto3
        if aws_secrets:
            for group_name, secret_name, secret_id in aws_secrets:
                secret_value = secrets_manager.get_secret_value(SecretId=secret_id)
                secret_payload = json.loads(secret_value["SecretString"])
                secrets[group_name][secret_name] = secret_payload[secret_name]
        # There is one secret settings that loads under django.users.
        # It contains usernames and corresponding (initial) passwords/tokens which we load upon Postgres setup.
        # We perform some tricks to load the dictionary correctly
        # from AWS into django.users configuration on host machines.
        if CONTEXT == "host":
            users_secret = secrets_manager.get_secret_value(SecretId=environment.django.users.usernames)
            users_payload = json.loads(users_secret["SecretString"])
            environment.django.users = users_payload  # will merge not overwrite
            environment._remove(("django", "users",), "usernames")  # removes the secret string among users

    return environment, session
