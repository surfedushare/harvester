import json
from sentry_sdk import capture_message

from django.conf import settings
from django.shortcuts import HttpResponse

from datagrowth.configuration import create_config
from harvester.utils.extraction import prepare_seed
from core.logging import HarvestLogger
from core.models import DatasetVersion


def get_seed_operation(seed, collection):
    document_exists = collection.document_set.filter(reference=seed["external_id"]).exists()
    if seed["state"] == "deleted" and document_exists:
        return "delete"
    elif seed["state"] == "deleted":
        return "ignore"
    elif document_exists:
        return "update"
    return "create"


def validate_webhook_data(request, set_specification, secret_key):
    """
    This function takes a webhook request and validates the source by looking at a secret
    and the IP addresses of the sender.
    If the request is valid it will return the raw data from the request in a Python format.
    If the request is invalid it will return a response with an appropriate message.

    :param request: the webhook request
    :param set_specification: the set specification that the webhook wants to update
    :param secret_key: the secret key from the request to identify the source
    :return: raw data or error response
    """
    configuration = settings.WEBHOOKS[set_specification]
    if str(secret_key) != configuration["secret"]:
        return HttpResponse(status=403, reason="Webhook not allowed in this environment"), configuration
    if request.META["HTTP_X_FORWARDED_FOR"] not in configuration["allowed_ips"]:
        capture_message(
            f"edit_document_webhook called from invalid IP: {request.META['HTTP_X_FORWARDED_FOR']}",
            level="warning"
        )
        return HttpResponse(status=403, reason="Webhook not allowed from source"), configuration
    try:
        return json.loads(request.body), configuration
    except json.decoder.JSONDecodeError:
        capture_message("edit_document_webhook received invalid JSON", level="warning")
        return HttpResponse(status=400, reason="Invalid JSON"), configuration


def get_webhook_destination(set_specification):
    """
    Retrieves the relevant Collection and current DatasetVersion for a given set_specification.
    These instances can be used to update the Document with the webhook data.

    :param set_specification: the set specification that the webhook wants to update
    :return: dataset_version and collection
    """
    dataset_version = DatasetVersion.objects.get_current_version()
    collection = dataset_version.collection_set.filter(name=set_specification).last()
    return dataset_version, collection


def extract_webhook_seed(extractor, objective, collection, data):
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
    operation = get_seed_operation(seed, collection)
    if operation == "create" and seed["language"] is None:
        seed["language"] = "unk"
    prepare_seed(seed)
    return seed, operation


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
        url=seed["url"],
        copyright=seed["copyright"],
        lowest_educational_level=seed["lowest_educational_level"]
    )
