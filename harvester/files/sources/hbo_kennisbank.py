from typing import Type, Iterator
import os
import bs4
from hashlib import sha1
from collections import namedtuple

from sources.utils.hbo_kennisbank import HBOKennisbankExtractor
from files.models import Set, FileDocument


FileInfo = namedtuple("FileInfo", ["product", "file", "item", "is_link"])


class HBOKennisbankFileExtractor(HBOKennisbankExtractor):

    #############################
    # OAI-PMH
    #############################

    @classmethod
    def get_oaipmh_record_state(cls, soup, info: FileInfo):
        return super().get_oaipmh_record_state(soup, info.product)

    #############################
    # EXTRACTION
    #############################

    @classmethod
    def get_url(cls, soup, info: FileInfo):
        if not info.file:
            return
        return cls.parse_url(info.file["ref"])

    @classmethod
    def get_hash(cls, soup, info: FileInfo):
        url = cls.get_url(soup, info)
        if not url:
            return
        return sha1(url.encode("utf-8")).hexdigest()

    @classmethod
    def get_product_id(cls, soup, info: FileInfo) -> str | None:
        return super().get_oaipmh_external_id(soup, info.product)

    @classmethod
    def get_external_id(cls, soup, info: FileInfo):
        file_hash = cls.get_hash(soup, info)
        if not file_hash:
            return
        parent_id = cls.get_product_id(soup, info)
        return f"{parent_id}:{file_hash}"

    @classmethod
    def get_mime_type(cls, soup, info: FileInfo):
        if not info.file:
            return
        return info.file.get("mimeType")

    @classmethod
    def get_copyright(cls, soup, info: FileInfo):
        default_copyright = super().get_copyright(soup, info.product)
        return default_copyright

    @classmethod
    def get_access_rights(cls, soup, info: FileInfo):
        if info.is_link:
            return "OpenAccess"
        if not info.file:
            return "ClosedAccess"
        access_rights_node = info.item.find("accessRights")
        _, access_rights = os.path.split(access_rights_node.text.strip())
        return access_rights

    @classmethod
    def get_provider(cls, soup, info: FileInfo):
        return super().get_provider(soup, info.product)


def get_file_infos(hbo_kennisbank_soup: bs4.BeautifulSoup) -> Iterator[FileInfo]:
    for product in HBOKennisbankExtractor.get_oaipmh_records(hbo_kennisbank_soup):
        # Handle files
        file_resources = HBOKennisbankExtractor.find_resources(product, "file")
        link_resources = HBOKennisbankExtractor.find_resources(product, "link")
        if not file_resources and not link_resources:
            yield FileInfo(product, None, None, False)
        for file_resource in file_resources:
            file_item = next((parent for parent in file_resource.parents if parent.name == "Item"), None)
            if not file_item:
                yield FileInfo(product, None, None, False)
            file_element = file_item.find("Resource")
            yield FileInfo(product, file_element, file_item, False)
        # Handle links
        for link_resource in link_resources:
            link_item = next((parent for parent in link_resource.parents if parent.name == "Item"), None)
            if not link_item:
                yield FileInfo(product, None, None, True)
            link_element = link_item.find("Resource")
            yield FileInfo(product, link_element, link_item, True)


def back_fill_deletes(seed: dict, harvest_set: Set) -> Iterator[dict]:
    if not seed["state"] == FileDocument.States.DELETED:
        yield seed
        return
    for doc in harvest_set.documents.filter(properties__product_id=seed["product_id"]):
        doc.properties["state"] = FileDocument.States.DELETED
        yield doc.properties


def build_objective(extract_processor: Type[HBOKennisbankFileExtractor]) -> dict:
    return {
        # Essential objective keys for system functioning
        "@": get_file_infos,
        "state": extract_processor.get_oaipmh_record_state,
        "external_id": extract_processor.get_external_id,
        "#set": extract_processor.get_oaipmh_set,
        # Generic metadata
        "url": extract_processor.get_url,
        "hash": extract_processor.get_hash,
        "mime_type": extract_processor.get_mime_type,
        "copyright": extract_processor.get_copyright,
        "access_rights": extract_processor.get_access_rights,
        "product_id": extract_processor.get_product_id,
        "is_link": lambda soup, info: info.is_link,
        "provider": extract_processor.get_provider,
    }
