import logging
from typing import Iterator
from hashlib import sha1
from collections import namedtuple


from sources.utils.edurep import EdurepExtractor
from files.models import Set, FileDocument


logger = logging.getLogger("harvester")

FileInfo = namedtuple("FileInfo", ["product", "mime_type", "url"])


def get_file_infos(edurep_soup) -> FileInfo:
    for product in EdurepExtractor.iterate_valid_products(edurep_soup):
        mime_types = product.find_all('czp:format')
        urls = product.find_all('czp:location')
        if not urls:
            yield FileInfo(product, None, None)
        for mime_type, url in zip(mime_types, urls):
            yield FileInfo(product, mime_type, url)


def back_fill_deletes(seed: dict, harvest_set: Set) -> Iterator[dict]:
    if not seed["state"] == FileDocument.States.DELETED:
        yield seed
        return
    for doc in harvest_set.documents.filter(properties__product_id=seed["product_id"]):
        doc.properties["state"] = FileDocument.States.DELETED
        yield doc.properties


class EdurepFileExtraction(object):

    @classmethod
    def get_state(cls, soup, info: FileInfo) -> str:
        return EdurepExtractor.get_oaipmh_record_state(info.product)

    @classmethod
    def get_hash(cls, soup, info: FileInfo) -> str | None:
        if not info.url:
            return
        url = EdurepExtractor.parse_url(info.url.text.strip())
        return sha1(url.encode("utf-8")).hexdigest()

    @classmethod
    def get_external_id(cls, soup, info: FileInfo) -> str | None:
        file_hash = cls.get_hash(soup, info)
        if not file_hash:
            return
        parent_id = cls.get_product_id(soup, info)
        return f"{parent_id}:{file_hash}"

    @classmethod
    def get_set(cls, soup, info: FileInfo) -> str | None:
        return f"edurep:{info.product.find('setSpec').text.strip()}"

    @classmethod
    def get_language(cls, soup, info: FileInfo):
        node = info.product.find('czp:language')
        return node.text.strip() if node else None

    @classmethod
    def get_url(cls, soup, info: FileInfo) -> str | None:
        if not info.url:
            return
        return EdurepExtractor.parse_url(info.url.text.strip())

    @classmethod
    def get_mime_type(cls, soup, info: FileInfo) -> str | None:
        if not info.mime_type or info.mime_type.text == "":
            return
        return info.mime_type.text.strip()

    @classmethod
    def get_copyright(cls, soup, info: FileInfo) -> str | None:
        return EdurepExtractor.get_copyright(info.product)

    @classmethod
    def get_product_id(cls, soup, info: FileInfo) -> str | None:
        return info.product.find('identifier').text.strip()

    @classmethod
    def get_access_rights(cls, soup, info: FileInfo) -> str | None:
        default_access_rights = "ClosedAccess"
        access_rights_blocks = EdurepExtractor.find_all_classification_blocks(info.product, "access rights", "czp:id")
        if len(access_rights_blocks):
            default_access_rights = access_rights_blocks[0].text.strip()
        return default_access_rights

    @classmethod
    def get_is_link(cls, soup, info: FileInfo) -> bool | None:
        if not info.mime_type:
            return
        return info.mime_type.text.strip() == "text/html"

    @classmethod
    def get_provider(cls, soup, info: FileInfo) -> dict | None:
        return EdurepExtractor.get_provider(info.product)


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": get_file_infos,
    "state": EdurepFileExtraction.get_state,
    "external_id": EdurepFileExtraction.get_external_id,
    "set": EdurepFileExtraction.get_set,
    "language": EdurepFileExtraction.get_language,
    # Generic metadata
    "url": EdurepFileExtraction.get_url,
    "hash": EdurepFileExtraction.get_hash,
    "mime_type": EdurepFileExtraction.get_mime_type,
    "copyright": EdurepFileExtraction.get_copyright,
    "access_rights": EdurepFileExtraction.get_access_rights,
    "product_id": EdurepFileExtraction.get_product_id,
    "is_link": EdurepFileExtraction.get_is_link,
    "provider": EdurepFileExtraction.get_provider
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
