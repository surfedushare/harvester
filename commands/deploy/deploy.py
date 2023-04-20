import boto3
from time import sleep

from invoke.tasks import task
from invoke.exceptions import Exit

from commands import TARGETS


def await_steady_fargate_services(ecs_client, cluster_name, services):
    steady_services = {service: False for service in services}
    sleep(30)
    while not all(steady_services.values()):
        fargate_state = ecs_client.describe_services(cluster=cluster_name, services=services)
        for service in fargate_state["services"]:
            last_event = next(iter(service["events"]), None)
            if not last_event:
                continue
            if "has reached a steady state" in last_event["message"]:
                steady_services[service["serviceName"]] = True
        sleep(10)


@task(help={
    "mode": "Mode you want to deploy to: development, acceptance or production. Must match APPLICATION_MODE"
})
def deploy(ctx, mode):
    """
    Updates the container cluster in development, acceptance or production environment on AWS to run a Docker image
    """
    target = ctx.config.service.name
    if target not in TARGETS:
        raise Exit(f"Unknown target: {target}", code=1)
    target_info = TARGETS[target]
    print(f"Starting deploy of {target}")

    print(f"Starting AWS session for: {mode}")
    session = boto3.Session(profile_name=ctx.config.aws.profile_name, region_name="eu-central-1")
    ecs_client = session.client('ecs')
    cluster_name = ctx.config.aws.cluster_name

    if target == "harvester":
        print("Deploying celery:", ctx.config.service.env)
        ecs_client.update_service(
            cluster=cluster_name,
            service="celery",
            taskDefinition="celery",
            forceNewDeployment=True,
        )
        print("Waiting for Celery to finish ... do not interrupt")
        await_steady_fargate_services(ecs_client, cluster_name, ["celery"])
        print("Deploying harvester:", ctx.config.service.env)
        ecs_client.update_service(
            cluster=cluster_name,
            service="harvester",
            taskDefinition="harvester",
            forceNewDeployment=True,
        )
    elif target == "service":
        print("Deploying search-portal:", ctx.config.service.env)
        ecs_client.update_service(
            cluster=cluster_name,
            service="search-portal",
            taskDefinition="search-portal",
            forceNewDeployment=True,
        )

    print("Waiting for deploy to finish ...")
    await_steady_fargate_services(ecs_client, cluster_name, [target_info["name"]])
    print("Done deploying")
