from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt


from sources.webhooks.utils import (validate_webhook_data, get_webhook_destination, extract_legacy_webhook_seed,
                                    commit_webhook_seed)
from sources.extraction.publinova import PublinovaMetadataExtraction, create_objective


@csrf_exempt
def legacy_edit_document_webhook(request, channel, secret):
    # Webhook validation
    data, configuration = validate_webhook_data(request, channel, secret)
    if isinstance(data, HttpResponse):
        return data
    # Fetches relevant containers from the database and creates objective
    dataset_version, collection = get_webhook_destination(channel)
    objective = create_objective(root="$")
    # Processing of incoming data
    seed, operation = extract_legacy_webhook_seed(PublinovaMetadataExtraction, objective, collection, data)
    if operation == "ignore":
        return HttpResponse("ignored")
    # Commit changes to the database and add to log
    commit_webhook_seed(dataset_version, collection, seed)
    # Finish webhook request
    return HttpResponse("ok")
