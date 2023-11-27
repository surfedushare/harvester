import os

from django.conf import settings


def extract_channel(response_data: dict) -> str | None:
    endpoint = response_data.get("links", {}).get("self", None)
    if not endpoint:
        return
    path, page = os.path.split(endpoint)
    _, channel = os.path.split(path)
    return f"sharekit:{channel}"


def extract_state(node: dict) -> str:
    attributes = node.get("attributes", {})
    default_state = "active"
    if attributes:
        provider_name = attributes.get("owner", {}).get("name", None)
        if provider_name and provider_name in settings.SHAREKIT_TEST_ORGANIZATION and \
                settings.ENVIRONMENT in ["acceptance", "production"]:
            default_state = "skipped"
    return node.get("meta", {}).get("status", default_state)


def webhook_data_transformer(webhook_data: dict, set_name: str):
    # Patches data coming from Sharekit webhook to be consistent
    # Deleted products will have an empty Array in the JSON instead of an Object
    if isinstance(webhook_data["attributes"], list):
        webhook_data["attributes"] = {}
    # Through the webhook we always only get one product,
    # while the extraction objectives also expect set_name information through the links property
    provider, channel_name = set_name.split(":")
    return {
        "links": {
            "self": f"/api/jsonapi/channel/v1/{channel_name}/webhook"
        },
        "data": [
            webhook_data
        ]
    }
