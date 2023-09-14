import os


def extract_channel(response_data: dict) -> str | None:
    endpoint = response_data.get("links", {}).get("self", None)
    if not endpoint:
        return
    path, page = os.path.split(endpoint)
    _, channel = os.path.split(path)
    return f"sharekit:{channel}"


def parse_url(url: str) -> str:
    url = url.strip()
    if url.startswith("ttp"):
        url = "h" + url
    url = url.replace(" ", "+")
    return url
