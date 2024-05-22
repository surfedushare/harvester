from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpRequest

from core.loading import load_source_configuration
from core.logging import HarvestLogger
from core.models.datatypes.document import HarvestDocument
from core.tasks.harvest.document import dispatch_document_tasks
from sources.webhooks.utils import validate_webhook_data, get_webhook_destination, commit_webhook_seeds


@csrf_exempt
def product_webhook(request: HttpRequest, source: str, set_specification: str, secret: str):
    # Set variables
    set_name = f"{source}:{set_specification}"
    # Webhook validation
    data, configuration = validate_webhook_data(request, set_name, secret)
    if isinstance(data, HttpResponse):
        return data
    # Fetches relevant containers from the database and creates objective
    for entity_type in ["products", "files"]:
        dataset_version, set_instance = get_webhook_destination(set_name, app_label=entity_type)
        if not dataset_version:
            return HttpResponse("No current dataset version", status=417)  # expectation failed
        configuration = load_source_configuration(entity_type, source)
        objective = configuration["objective"]
        logger = HarvestLogger(dataset_version.dataset.name, "product_webhook", {}, is_legacy_logger=False)
        # Processing and storage of incoming data
        documents = commit_webhook_seeds(objective, data, set_instance, configuration)
        dispatch_document_tasks.delay(
            entity_type,
            [doc.id for doc in documents if doc.state != HarvestDocument.States.DELETED]
        )
        for document in documents:
            logger.report_document(
                document.identity,
                entity_type,
                state=document.state,
                title=document.properties.get("title", None)
            )
    # Finish webhook request
    return HttpResponse("ok")
