import os

from django.conf import settings


def extract_channel(response_data: dict) -> str | None:
    endpoint = response_data.get("links", {}).get("self", None)
    if not endpoint:
        return
    path, page = os.path.split(endpoint)
    _, channel = os.path.split(path)
    return f"sharekit:{channel}"


def parse_url(url: str) -> str | None:
    if not url:
        return
    url = url.strip()
    url = url.replace(" ", "+")
    return url


def extract_state(node: dict) -> str:
    attributes = node.get("attributes", {})
    default_state = "active"
    if attributes:
        provider_name = attributes.get("owner", {}).get("name", None)
        if provider_name and provider_name in settings.SHAREKIT_TEST_ORGANIZATION and \
                settings.ENVIRONMENT in ["acceptance", "production"]:
            default_state = "skipped"
    return node.get("meta", {}).get("status", default_state)
