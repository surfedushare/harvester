import json
import boto3
from time import sleep

from invoke.tasks import task
from invoke.exceptions import Exit

from environments.project import MODE, FARGATE_CLUSTER_NAME
from commands import TARGETS
from commands.aws.ecs import register_task_definition, build_default_container_variables, list_running_containers


def register_scheduled_tasks(ctx, aws_config, task_definition_arn):
    session = boto3.Session(profile_name=ctx.config.aws.profile_name, region_name="eu-central-1")
    events_client = session.client('events')
    iam = session.resource('iam')
    role = iam.Role('ecsEventsRole')
    ecs_parameters = {
        'TaskDefinitionArn': task_definition_arn,
        'TaskCount': 1,
        'LaunchType': 'FARGATE',
        'NetworkConfiguration': {
            "awsvpcConfiguration": {
                "Subnets": [aws_config.private_subnet_id],
                "SecurityGroups": [
                    aws_config.rds_security_group_id,
                    aws_config.default_security_group_id

                ]
            }
        }
    }
    scheduled_tasks = [
        (task, str(ix+1), ["python", "manage.py", task])
        for ix, task in enumerate(ctx.config.aws.scheduled_tasks)
    ]
    for rule, identifier, command in scheduled_tasks:
        events_client.put_targets(
            Rule=rule,
            Targets=[
                {
                    'Id': identifier,
                    'Arn': aws_config.cluster_arn,
                    'RoleArn': role.arn,
                    'Input': json.dumps(
                        {
                            "containerOverrides": [
                                {
                                    "name": "search-portal-container",
                                    "command": command
                                }
                            ]
                        }
                    ),
                    'EcsParameters': ecs_parameters
                }
            ]
        )


def await_steady_fargate_services(ecs_client, services):
    steady_services = {service: False for service in services}
    sleep(30)
    while not all(steady_services.values()):
        fargate_state = ecs_client.describe_services(cluster=FARGATE_CLUSTER_NAME, services=services)
        for service in fargate_state["services"]:
            last_event = next(iter(service["events"]), None)
            if not last_event:
                continue
            if "has reached a steady state" in last_event["message"]:
                steady_services[service["serviceName"]] = True
        sleep(10)


def _legacy_deploy_harvester(ctx, mode, ecs_client, task_role_arn, version):
    target_info = TARGETS["harvester"]
    harvester_container_variables = build_default_container_variables(mode, version)
    harvester_container_variables.update({
        "flower_secret_arn": ctx.config.aws.flower_secret_arn,
        "harvester_bucket": ctx.config.aws.harvest_content_bucket
    })

    harvester_task_definition_arn = register_task_definition(
        "harvester",
        ecs_client,
        task_role_arn,
        harvester_container_variables,
        True,
        target_info["cpu"],
        target_info["memory"]
    )

    ecs_client.update_service(
        cluster=ctx.config.aws.cluster_arn,
        service="harvester",
        taskDefinition=harvester_task_definition_arn
    )


def deploy_harvester(ctx, mode, ecs_client, task_role_arn, version, legacy_system):
    if legacy_system:
        _legacy_deploy_harvester(ctx, mode, ecs_client, task_role_arn, version)
        return
    ecs_client.update_service(
        cluster=FARGATE_CLUSTER_NAME,
        service="harvester",
        taskDefinition="harvester",
        forceNewDeployment=True,
    )


def _legacy_deploy_celery(ctx, mode, ecs_client, task_role_arn, version):
    target_info = TARGETS["harvester"]
    celery_container_variables = build_default_container_variables(mode, version)
    celery_container_variables.update({
        "concurrency": "4",
        "harvester_bucket": ctx.config.aws.harvest_content_bucket
    })

    celery_task_definition_arn = register_task_definition(
        "celery",
        ecs_client,
        task_role_arn,
        celery_container_variables,
        False,
        target_info["celery_cpu"],
        target_info["celery_memory"]
    )

    ecs_client.update_service(
        cluster=ctx.config.aws.cluster_arn,
        service="celery",
        taskDefinition=celery_task_definition_arn
    )


def deploy_celery(ctx, mode, ecs_client, task_role_arn, version, legacy_system):
    if legacy_system:
        _legacy_deploy_celery(ctx, mode, ecs_client, task_role_arn, version)
        return
    ecs_client.update_service(
        cluster=FARGATE_CLUSTER_NAME,
        service="celery",
        taskDefinition="celery",
        forceNewDeployment=True,
    )


def _legacy_deploy_service(ctx, mode, ecs_client, task_role_arn, version):
    target_info = TARGETS["service"]
    service_container_variables = build_default_container_variables(mode, version)

    print("Registering task definition")
    service_task_definition_arn = register_task_definition(
        target_info['name'],
        ecs_client,
        task_role_arn,
        service_container_variables,
        True,
        target_info["cpu"],
        target_info["memory"]
    )

    print("Updating service")
    ecs_client.update_service(
        cluster=ctx.config.aws.cluster_arn,
        service=target_info['name'],
        taskDefinition=service_task_definition_arn
    )

    print("Registering scheduled tasks")
    register_scheduled_tasks(ctx, ctx.config.aws, service_task_definition_arn)


def deploy_service(ctx, mode, ecs_client, task_role_arn, version, legacy_system):
    if legacy_system:
        _legacy_deploy_service(ctx, mode, ecs_client, task_role_arn, version)
        return
    ecs_client.update_service(  # please note that non-legacy deploys skip update of scheduled tasks
        cluster=FARGATE_CLUSTER_NAME,
        service="search-portal",
        taskDefinition="search-portal",
        forceNewDeployment=True,
    )


@task(help={
    "mode": "Mode you want to deploy to: development, acceptance or production. Must match APPLICATION_MODE",
    "version": "Version of the project you want to deploy. Defaults to latest version",
    "legacy_system": "Whether to deploy by creating a new task definition. For backward compatibility only."
})
def deploy(ctx, mode, version=None, legacy_system=True):
    """
    Updates the container cluster in development, acceptance or production environment on AWS to run a Docker image
    """
    target = ctx.config.service.name
    if target not in TARGETS:
        raise Exit(f"Unknown target: {target}", code=1)

    print(f"Starting deploy of {target}")

    target_info = TARGETS[target]
    version = version or target_info["version"]
    task_role_arn = ctx.config.aws.task_role_arn

    print(f"Starting AWS session for: {mode}")
    session = boto3.Session(profile_name=ctx.config.aws.profile_name, region_name="eu-central-1")
    ecs_client = session.client('ecs')

    if target == "harvester":
        print(f"Deploying Celery version {version}")
        deploy_celery(ctx, mode, ecs_client, task_role_arn, version, legacy_system)
        print("Waiting for Celery to finish ... do not interrupt")
        await_steady_fargate_services(ecs_client, ["celery"])
        print(f"Deploying harvester version {version}")
        deploy_harvester(ctx, mode, ecs_client, task_role_arn, version, legacy_system)
    elif target == "service":
        print(f"Deploying service version {version}")
        deploy_service(ctx, mode, ecs_client, task_role_arn, version, legacy_system)

    print("Waiting for deploy to finish ...")
    await_steady_fargate_services(ecs_client, [target_info["name"]])
    print("Done deploying")


@task(help={
    "target": "Name of the project you want to list versions for: service or harvester",
    "mode": "Mode you want to list versions for: development, acceptance or production. Must match APPLICATION_MODE",
})
def print_running_containers(ctx, target, mode):
    # Check the input for validity
    if target not in TARGETS:
        raise Exit(f"Unknown target: {target}", code=1)
    if mode != MODE:
        raise Exit(f"Expected mode to match APPLICATION_MODE value but found: {mode}", code=1)

    # Load info
    target_info = TARGETS[target]
    name = target_info["name"]

    # Start boto
    session = boto3.Session(profile_name=ctx.config.aws.profile_name)
    ecs = session.client("ecs")

    # List images
    running_containers = list_running_containers(ecs, ctx.config.aws.cluster_arn, name)
    print(json.dumps(running_containers, indent=4))
