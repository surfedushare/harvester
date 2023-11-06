import logging
from typing import Iterator
from hashlib import sha1

from vobject.base import ParseError, readOne

from core.constants import HIGHER_EDUCATION_LEVELS, MBO_EDUCATIONAL_LEVELS
from sources.utils.sharekit import extract_channel, parse_url, extract_state, webhook_data_transformer
from files.models import Set, FileDocument


logger = logging.getLogger("harvester")


def find_all_classification_blocks(element, classification_type, output_type):
    assert output_type in ["czp:entry", "czp:id"]
    entries = element.find_all(string=classification_type)
    blocks = []
    for entry in entries:
        classification_element = entry.find_parent('czp:classification')
        if not classification_element:
            continue
        blocks += classification_element.find_all(output_type)
    return blocks

def parse_vcard_element(record, external_id):
    card = "\n".join(field.strip() for field in record.text.strip().split("\n"))
    try:
        return readOne(card)
    except ParseError:
        logger.warning(f"Can't parse vCard for material with id: {external_id}")
        return

def get_publishers(product, external_id):
    publishers = []
    publisher_element = product.find(string='publisher')
    if not publisher_element:
        return publishers
    contribution_element = publisher_element.find_parent('czp:contribute')
    if not contribution_element:
        return publishers
    nodes = contribution_element.find_all('czp:vcard')
    for node in nodes:
        publisher = parse_vcard_element(node, external_id)
        if hasattr(publisher, "fn"):
            publishers.append(publisher.fn.value)
    return publishers

def get_provider_name(product, external_id):
    provider_name = None
    publishers = get_publishers(product, external_id)
    if len(publishers):
        provider_name = publishers[0]
    return provider_name


def _get_educational_level_state(product):
    """
    Returns the desired state of the record based on (non NL-LOM) educational levels
    """
    blocks = find_all_classification_blocks(product, "educational level", "czp:entry")
    educational_levels = list(set([block.find('czp:langstring').text.strip() for block in blocks]))
    if not len(educational_levels):
        return "inactive"
    has_higher_level = False
    has_lower_level = False
    for education_level in educational_levels:
        is_higher_level = False
        is_lower_level = False
        for higher_education_level in HIGHER_EDUCATION_LEVELS.keys():
            if education_level.startswith(higher_education_level):
                is_higher_level = True
                break
        for mbo_education_level in MBO_EDUCATIONAL_LEVELS:
            if education_level.startswith(mbo_education_level):
                break
        else:
            # The level is not MBO ... so it has to be lower level if it's not higher level
            is_lower_level = not is_higher_level
        # If any education_level matches against higher than HBO or lower than MBO
        # Then we mark the material as higher_level and/or lower_level
        has_higher_level = has_higher_level or is_higher_level
        has_lower_level = has_lower_level or is_lower_level
    # A record needs to have at least one "higher education" level
    # and should not have any "children education" levels
    return "active" if has_higher_level and not has_lower_level else "inactive"

def get_oaipmh_record_state(product):
    """
    Returns the state specified by the record or calculates state based on (non NL-LOM) educational level
    """
    educational_level_state = _get_educational_level_state(product)
    header = product.find('header')
    return header.get("status", educational_level_state)

def get_file_seeds(edurep_soup):
    """
    This function takes a Sharekit publication API response and transforms it into file dicts.
    File dicts have at least an "url" key that indicates where we can find the file.
    The "srn" key contains a unique identifier for the "url".
    The "is_link" key indicates whether we should treat the "url" as an actual link instead of a file link.

    :param edurep_soup: a parsed Sharekit publication API response
    :return: yields file objects
    """
    for product in edurep_soup.find_all('record'):
        product_id = product.find('identifier').text.strip()
        product_set = product.find('setSpec').text.strip()
        product_copyright = find_all_classification_blocks(product, "access rights", "czp:id")
        product_provider_name = get_provider_name(product, external_id=product_id)
        mime_types = product.find_all('czp:format')
        urls = product.find_all('czp:location')
        if not urls:
            yield {
                "url": None,
                "state": "deleted",
                "set": product_set,
                "product": {
                    "provider": product_provider_name,
                    "product_id": product_id,
                    "copyright": product_copyright
                }
            }
            return
        file_info_iterator = zip(
            [mime_node.text.strip() for mime_node in mime_types],
            [url_node.text.strip() for url_node in urls],
            [f"URL {ix + 1}" for ix, mime_node in enumerate(mime_types)],
        )
        for mime_type, url, title in file_info_iterator:
            if not url:
                continue
            product_file = {}
            product_file["state"] = get_oaipmh_record_state(product)
            product_file["set"] = product_set
            # We add some product metadata, because unfortunately the product supplies defaults
            product_file["product"] = {
                "provider": product_provider_name,
                "product_id": product_id,
                "copyright": product_copyright
            }
            # We indicate we're not dealing with a webpage URL
            product_file["is_link"] = mime_type == "text/html"
            yield product_file


def back_fill_deletes(seed: dict, harvest_set: Set) -> Iterator[dict]:
    if not seed["state"] == FileDocument.States.DELETED.value:
        yield seed
        return
    for doc in harvest_set.documents.filter(properties__product_id=seed["product_id"]):
        doc.properties["state"] = FileDocument.States.DELETED.value
        yield doc.properties


class SharekitFileExtraction(object):

    @classmethod
    def get_hash(cls, soup, el) -> str | None:
        url = parse_url(el.get("id", None))
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
    # "state": lambda node: node["state"],
    "external_id": SharekitFileExtraction.get_hash,
    # "set": lambda node: node["set"],
    # # Generic metadata
    # "url": lambda node: parse_url(node["url"]),
    # "hash": SharekitFileExtraction.get_hash,
    # "mime_type": SharekitFileExtraction.get_mime_type,
    # "title": lambda node: node.get("fileName", node.get("urlName", None)),
    # "copyright": lambda node: node["product"]["copyright"],
    # "access_rights": SharekitFileExtraction.get_access_rights,
    # "product_id": lambda node: node["product"]["product_id"],
    # "is_link": lambda node: node.get("is_link", None),
    # "provider": lambda node: node["product"]["provider"]
}


SEEDING_PHASES = [
    {
        "phase": "publications",
        "strategy": "initial",
        "batch_size": 25,
        "retrieve_data": {
            "resource": "sources.EdurepOAIPMH",
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
