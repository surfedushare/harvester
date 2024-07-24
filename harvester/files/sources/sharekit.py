from typing import Iterator
from hashlib import sha1
from collections import namedtuple

from sources.utils.sharekit import SharekitExtractor
from files.models import Set, FileDocument


FileInfo = namedtuple("FileInfo", ["product", "file", "is_link", "channel"])


def get_file_info(sharekit_products_data: dict) -> Iterator[FileInfo]:
    """
    This function takes a Sharekit publication API response and transforms it into FileInfo tuples.
    A FileInfo tuple holds the Product dict that contains the file.
    As well as a file dict with some file information or None if a Product has no files.
    FileInfo indicates if a file was originally a link by setting is_link to True.
    Lastly FileInfo holds the channel information, which is the name of the set the files are part of.

    :param sharekit_products_data: a parsed Sharekit publication API response
    :return: yields FileInfo tuples
    """
    channel = SharekitExtractor.extract_channel(sharekit_products_data)
    for product in sharekit_products_data["data"]:
        product_attributes = product["attributes"]
        product_files = product_attributes.get("files", []) or []
        product_links = product_attributes.get("links", []) or []
        if not product_files and not product_links:
            yield FileInfo(product, None, False, channel)
        for product_file in product_files:
            yield FileInfo(product, product_file, False, channel)
        for product_link in product_links:
            yield FileInfo(product, product_link, True, channel)


def back_fill_deletes(seed: dict, harvest_set: Set) -> Iterator[dict]:
    if not seed["state"] == FileDocument.States.DELETED:
        yield seed
        return
    for doc in harvest_set.documents.filter(properties__product_id=seed["product_id"]):
        doc.properties["state"] = FileDocument.States.DELETED
        yield doc.properties


class SharekitFileExtraction(object):

    @classmethod
    def get_state(cls, info: FileInfo) -> str:
        if not info.file:
            return FileDocument.States.DELETED
        return SharekitExtractor.extract_state(info.product)

    @classmethod
    def get_url(cls, info: FileInfo) -> str | None:
        if not info.file:
            return
        return SharekitExtractor.parse_url(info.file["url"])

    @classmethod
    def get_hash(cls, info: FileInfo) -> str | None:
        if not info.file:
            return
        etag = info.file.get("eTag")
        if not etag or not etag.startswith("\"") or not etag.endswith("\""):
            etag = None
        if etag:
            file_hash = etag.strip("\"")
        else:
            url = cls.get_url(info)
            file_hash = sha1(url.encode("utf-8")).hexdigest() if url else None
        return file_hash

    @classmethod
    def get_external_id(cls, info: FileInfo) -> str | None:
        if not info.file:
            return
        url = cls.get_url(info)
        if not url:
            return
        url_hash = sha1(url.encode("utf-8")).hexdigest()
        return f"{info.product['id']}:{url_hash}"

    @classmethod
    def get_mime_type(cls, info: FileInfo) -> str | None:
        if not info.file:
            return
        mime_type = info.file.get("resourceMimeType", None)
        if mime_type is None and info.is_link:
            mime_type = "text/html"
        return mime_type

    @classmethod
    def get_title(cls, info: FileInfo) -> str | None:
        if not info.file:
            return
        elif info.is_link:
            return info.file.get("urlName")
        else:
            return info.file.get("fileName")

    @classmethod
    def get_copyright(cls, info: FileInfo) -> str | None:
        if not info.file:
            return info.product["attributes"].get("termsOfUse")
        return info.file.get("usageRight") or info.product["attributes"].get("termsOfUse")

    @classmethod
    def get_access_rights(cls, info: FileInfo) -> str | None:
        if not info.file:
            return
        access_rights = info.file.get("accessRight", None)
        if not access_rights:
            return
        if access_rights[0].isupper():  # value according to standard; no parsing necessary
            return access_rights
        access_rights = access_rights.replace("access", "")
        access_rights = access_rights.capitalize()
        access_rights += "Access"
        return access_rights

    @classmethod
    def get_provider(cls, info: FileInfo) -> str | None:
        publishers = info.product["attributes"].get("publishers", []) or []
        if isinstance(publishers, str):
            publishers = [publishers]
        return publishers[0] if len(publishers) else "sharekit"

    @classmethod
    def get_priority(cls, info: FileInfo) -> int:
        if not info.file:
            return 0
        important_value = info.file.get("important", "0")
        if important_value is None or not important_value.isnumeric():
            return 0
        return int(important_value)


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": get_file_info,
    "state": SharekitFileExtraction.get_state,
    "external_id": SharekitFileExtraction.get_external_id,
    "set": lambda info: info.channel,
    # Generic metadata
    "url": SharekitFileExtraction.get_url,
    "hash": SharekitFileExtraction.get_hash,
    "mime_type": SharekitFileExtraction.get_mime_type,
    "title": SharekitFileExtraction.get_title,
    "copyright": SharekitFileExtraction.get_copyright,
    "access_rights": SharekitFileExtraction.get_access_rights,
    "product_id": lambda info: info.product["id"],
    "is_link": lambda info: info.is_link,
    "provider": SharekitFileExtraction.get_provider,
    "priority": SharekitFileExtraction.get_priority,
}


SEEDING_PHASES = [
    {
        "phase": "publications",
        "strategy": "initial",
        "batch_size": 25,
        "retrieve_data": {
            "resource": "sources.sharekitmetadataharvest",
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


WEBHOOK_DATA_TRANSFORMER = SharekitExtractor.webhook_data_transformer


SEQUENCE_PROPERTIES = {  # with tests these properties are used to generate mock data
    "external_id": "{ix}",
    "set": "sharekit:test",
    "url": "http://testserver/{ix}",
    "hash": "{ix}",
}
