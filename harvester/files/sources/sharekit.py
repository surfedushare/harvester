from typing import Iterator
from hashlib import sha1

from sources.utils.sharekit import extract_channel, parse_url, extract_state, webhook_data_transformer
from files.models import Set, FileDocument


def get_file_seeds(sharekit_products_data: dict):
    """
    This function takes a Sharekit publication API response and transforms it into file dicts.
    File dicts have at least an "url" key that indicates where we can find the file.
    The "srn" key contains a unique identifier for the "url".
    The "is_link" key indicates whether we should treat the "url" as an actual link instead of a file link.

    :param sharekit_products_data: a parsed Sharekit publication API response
    :return: yields file objects
    """
    channel = extract_channel(sharekit_products_data)
    for sharekit_product in sharekit_products_data["data"]:
        product_id = sharekit_product["id"]
        product_attributes = sharekit_product["attributes"]
        product_copyright = product_attributes.get("termsOfUse", None)
        product_publishers = product_attributes.get("publishers", []) or []
        product_provider_name = product_publishers[0] if len(product_publishers) else "sharekit"
        product_files = product_attributes.get("files", []) or []
        product_links = product_attributes.get("links", []) or []
        # Yield delete data if files and links are missing
        if not product_files and not product_links:
            yield {
                "url": None,
                "state": "deleted",
                "set": channel,
                "product": {
                    "provider": product_provider_name,
                    "product_id": product_id,
                    "copyright": product_copyright
                }
            }
        # Yield files data
        for product_file in product_files:
            # Anything without a URL can not be processed
            if not product_file.get("url", None):
                continue
            product_file["state"] = extract_state(sharekit_product)
            product_file["set"] = channel
            # We add some product metadata, because unfortunately the product supplies defaults
            product_file["product"] = {
                "provider": product_provider_name,
                "product_id": product_id,
                "copyright": product_copyright
            }
            # We indicate we're not dealing with a webpage URL
            product_file["is_link"] = False
            yield product_file
        # Yield links data
        for product_link in product_links:
            # Anything without a URL can not be processed
            if not product_link.get("url", None):
                continue
            product_link["state"] = extract_state(sharekit_product)
            product_link["set"] = channel
            product_link["product"] = {
                "provider": "sharekit",
                "product_id": product_id,
                "copyright": product_copyright
            }
            # We indicate that the URL points to a webpage
            product_link["is_link"] = True
            yield product_link


def back_fill_deletes(seed: dict, harvest_set: Set) -> Iterator[dict]:
    if not seed["state"] == FileDocument.States.DELETED.value:
        yield seed
        return
    for doc in harvest_set.documents.filter(properties__product_id=seed["product_id"]):
        doc.properties["state"] = FileDocument.States.DELETED.value
        yield doc.properties


class SharekitFileExtraction(object):

    @classmethod
    def get_hash(cls, node: dict) -> str | None:
        url = parse_url(node["url"])
        if not url:
            return
        return sha1(url.encode("utf-8")).hexdigest()

    @classmethod
    def get_mime_type(cls, node: dict) -> str:
        mime_type = node.get("resourceMimeType", None)
        if mime_type is None and node.get("is_link", None):
            mime_type = "text/html"
        return mime_type

    @classmethod
    def get_access_rights(cls, node: dict) -> str | None:
        access_rights = node.get("accessRight", None)
        if not access_rights:
            return
        if access_rights[0].isupper():  # value according to standard; no parsing necessary
            return access_rights
        access_rights = access_rights.replace("access", "")
        access_rights = access_rights.capitalize()
        access_rights += "Access"
        return access_rights


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": get_file_seeds,
    "state": lambda node: node["state"],
    "external_id": SharekitFileExtraction.get_hash,
    "set": lambda node: node["set"],
    # Generic metadata
    "url": lambda node: parse_url(node["url"]),
    "hash": SharekitFileExtraction.get_hash,
    "mime_type": SharekitFileExtraction.get_mime_type,
    "title": lambda node: node.get("fileName", node.get("urlName", None)),
    "copyright": lambda node: node["product"]["copyright"],
    "access_rights": SharekitFileExtraction.get_access_rights,
    "product_id": lambda node: node["product"]["product_id"],
    "is_link": lambda node: node.get("is_link", None),
    "provider": lambda node: node["product"]["provider"]
}


SEEDING_PHASES = [
    {
        "phase": "publications",
        "strategy": "initial",
        "batch_size": 25,
        "retrieve_data": {
            "resource": "sharekit.sharekitmetadataharvest",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    },
    {
        "phase": "deletes",
        "strategy": "back_fill",
        "batch_size": 25,
        "contribute_data": {
            "callback": back_fill_deletes
        },
        "is_post_initialization": True
    }
]


WEBHOOK_DATA_TRANSFORMER = webhook_data_transformer
