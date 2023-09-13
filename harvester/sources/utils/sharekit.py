import os


def extract_channel(response_data: dict) -> str | None:
    endpoint = response_data.get("links", {}).get("self", None)
    if not endpoint:
        return
    path, page = os.path.split(endpoint)
    _, channel = os.path.split(path)
    return f"sharekit:{channel}"
