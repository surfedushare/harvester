import json
from sentry_sdk import capture_message

from django.conf import settings
from django.shortcuts import HttpResponse

from datagrowth.configuration import create_config
from datagrowth.processors import ExtractProcessor
from harvester.utils.extraction import prepare_seed
from core.logging import HarvestLogger
from core.loading import load_harvest_models
from core.models.datatypes import HarvestSet, HarvestDocument
from core.processors.seed.resource import HttpSeedingProcessor


def get_legacy_seed_operation(seed, collection):
    document_exists = collection.document_set.filter(reference=seed["external_id"]).exists()
    if seed["state"] == "deleted" and document_exists:
        return "delete"
    elif seed["state"] == "deleted":
        return "ignore"
    elif document_exists:
        return "update"
    return "create"


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


def extract_legacy_webhook_seed(extractor, objective, collection, data):
    """
    Extracts the relevant data from the raw data

    :param extractor: ExtractProcessor to use
    :param objective: mapping to extract relevant data
    :param collection: Collection that might already contain incoming data
    :param data: the raw data to extract from
    :return: data to be stored into the system (known as a "seed")
    """
    extract_config = create_config("extract_processor", {
        "objective": objective
    })
    prc = extractor(config=extract_config)
    seed = next(prc.extract("application/json", data))
    operation = get_legacy_seed_operation(seed, collection)
    if operation == "create" and seed["language"] is None:
        seed["language"] = "unk"
    prepare_seed(seed)
    return seed, operation


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


def commit_webhook_seed(dataset_version, collection, seed):
    """
    Commits data to the relevant collection and logs the update to the HarvestLogger.

    :param dataset_version: the dataset_version to commit to
    :param collection: the collection to commit to
    :param seed: the data to commit
    :return: None
    """
    collection.update([seed], "external_id")
    logger = HarvestLogger(dataset_version.dataset.name, "edit_document_webhook", {})
    logger.report_material(
        seed["external_id"],
        state=seed["state"],
        title=seed["title"],
        url=seed["url"]
    )
