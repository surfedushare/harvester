import logging
from typing import Iterator
from hashlib import sha1
from collections import namedtuple

from vobject.base import ParseError, readOne

from core.constants import HIGHER_EDUCATION_LEVELS, MBO_EDUCATIONAL_LEVELS
from sources.utils.edurep import EdurepExtractor
from sources.utils.sharekit import extract_channel, parse_url, extract_state, webhook_data_transformer
from files.models import Set, FileDocument


logger = logging.getLogger("harvester")

FileInfo = namedtuple("FileInfo", ["product", "mime_type", "url"])



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




def get_file_infos(edurep_soup) -> FileInfo:
    for product in edurep_soup.find_all('record'):
        mime_types = product.find_all('czp:format')
        urls = product.find_all('czp:location')
        if not urls:
            continue
        for mime_type, url in zip(mime_types, urls):
            yield FileInfo(product, mime_type, url)




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
        product_copyright = EdurepExtractor.find_all_classification_blocks(product, "access rights", "czp:id")
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
            product_file["state"] = EdurepExtractor.get_oaipmh_record_state(product)
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


class EdurepFileExtraction(object):

    @classmethod
    def get_state(cls, soup, info: FileInfo) -> str | None:
        return EdurepExtractor.get_oaipmh_record_state(info.product)

    @classmethod
    def get_hash(cls, soup, info: FileInfo) -> str | None:
        url = parse_url(info.url.text.strip())
        if not url:
            return
        return sha1(url.encode("utf-8")).hexdigest()

    @classmethod
    def get_set(cls, soup, info: FileInfo) -> str | None:
        return info.product.find('setSpec').text.strip()

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

    @classmethod
    def get_url(cls, soup, info: FileInfo) -> str | None:
        return parse_url(info.url.text.strip())

    @classmethod
    def get_mime_type(cls, soup, info: FileInfo) -> str | None:
        return info.mime_type

    @classmethod
    def get_copyright(cls, soup, info: FileInfo) -> str | None:
        return EdurepExtractor.get_copyright(info.product)





OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": get_file_infos,
    "state": EdurepFileExtraction.get_state,
    "external_id": EdurepFileExtraction.get_hash,
    "set": EdurepFileExtraction.get_set,
    # # Generic metadata
    "url": EdurepFileExtraction.get_url,
    "hash": EdurepFileExtraction.get_hash,
    "mime_type": EdurepFileExtraction.get_mime_type,
    # "title": lambda node: node.get("fileName", node.get("urlName", None)),
    "copyright": EdurepFileExtraction.get_copyright,
    # "access_rights": EdurepFileExtraction.get_access_rights,
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
