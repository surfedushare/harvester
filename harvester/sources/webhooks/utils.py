import json
from sentry_sdk import capture_message

from django.conf import settings
from django.shortcuts import HttpResponse

from datagrowth.configuration import create_config
from datagrowth.processors import ExtractProcessor
from core.loading import load_harvest_models
from core.models.datatypes import HarvestSet, HarvestDocument
from core.processors.seed.resource import HttpSeedingProcessor


def validate_webhook_data(request, set_name, secret_key):
    """
    This function takes a webhook request and validates the source by looking at a secret
    and the IP addresses of the sender.
    If the request is valid it will return the raw data from the request in a Python format.
    If the request is invalid it will return a response with an appropriate message.

    :param request: the webhook request
    :param set_name: the set name that the webhook wants to update
    :param secret_key: the secret key from the request to identify the source
    :return: raw data or error response
    """
    configuration = settings.WEBHOOKS[set_name]
    if str(secret_key) != configuration["secret"]:
        return HttpResponse(status=403, reason="Webhook not allowed in this environment"), configuration
    if request.META["HTTP_X_FORWARDED_FOR"] not in configuration["allowed_ips"]:
        capture_message(
            f"Webhook called from invalid IP: {request.META['HTTP_X_FORWARDED_FOR']}",
            level="warning"
        )
        return HttpResponse(status=403, reason="Webhook not allowed from source"), configuration
    try:
        return json.loads(request.body), configuration
    except json.decoder.JSONDecodeError:
        capture_message("Webhook received invalid JSON", level="warning")
        return HttpResponse(status=400, reason="Invalid JSON"), configuration


def get_webhook_destination(set_name, app_label="core"):
    """
    Retrieves the relevant Collection and current DatasetVersion for a given set_specification.
    These instances can be used to update the Document with the webhook data.

    :param set_name: the set name that the webhook wants to update
    :param app_label: the app label of the entity that the webhook wants to update (default is core)
    :return: dataset_version and the set (previously collection)
    """
    models = load_harvest_models(app_label)
    DatasetVersion = models["DatasetVersion"]
    dataset_version = DatasetVersion.objects.get_current_version()
    if not dataset_version:
        return None, None
    set_instance = dataset_version.sets.filter(name=set_name).last()
    return dataset_version, set_instance


def commit_webhook_seeds(objective: dict, webhook_data: dict, set_instance: HarvestSet,
                         source_configuration: dict) -> list[HarvestDocument]:
    """
    Extracts the relevant data from the raw webhook data and commits the seeds as Documents

    :param objective: mapping to extract relevant data
    :param webhook_data: the webhook data to extract seeds from
    :param set_instance: the set instance to commit the data to
    :param source_configuration: the configuration of the source of the webhook
    :return: the Documents that were upserted
    """
    # Transform raw data to something the system can work with
    webhook_transformer = source_configuration["webhook_data_transformer"]
    data = webhook_data if not webhook_transformer else webhook_transformer(webhook_data, set_instance.name)
    # Extract seeds
    extract_config = create_config("extract_processor", {
        "objective": objective
    })
    extractor = ExtractProcessor(config=extract_config)
    seed_content = list(extractor.extract("application/json", data))
    # Commit seeds using the same processor that processes other data from the source
    # We'll return the outcome of the commits
    seeding_config = create_config("seeding_processor", {
        "phases": source_configuration["seeding_phases"]
    })
    seeder = HttpSeedingProcessor(set_instance, seeding_config, initial=seed_content)
    documents = []
    for batch in seeder():
        for doc in batch:
            documents.append(doc)
    return documents
