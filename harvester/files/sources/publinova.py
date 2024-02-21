from typing import Iterator
from dataclasses import dataclass
from hashlib import sha1

from sources.utils.publinova import PublinovaExtractor
from files.models import Set, FileDocument


@dataclass(frozen=True, slots=True)
class FileInfo:
    file: dict | None
    product: dict


def get_file_info(publinova_data: dict) -> Iterator[FileInfo]:
    for product in publinova_data["data"]:
        files = product.get("files", [])
        if not files:
            yield FileInfo(file=None, product=product)
            continue
        for file_object in files:
            yield FileInfo(
                file=file_object,
                product=product,
            )


def back_fill_deletes(seed: dict, harvest_set: Set) -> Iterator[dict]:
    if not seed["state"] == FileDocument.States.DELETED:
        yield seed
        return
    for doc in harvest_set.documents.filter(properties__product_id=seed["product_id"]):
        doc.properties["state"] = FileDocument.States.DELETED
        yield doc.properties


class PublinovaFileExtraction(PublinovaExtractor):

    @classmethod
    def get_product_state(cls, info: FileInfo):
        return info.product.get("state", "active")

    #############################
    # GENERIC
    #############################

    @classmethod
    def get_url(cls, info: FileInfo) -> str | None:
        if info.file is None:
            return
        return cls.parse_url(info.file["url"])

    @classmethod
    def get_hash(cls, info: FileInfo) -> str | None:
        url = cls.get_url(info)
        if url is None:
            return
        return sha1(url.encode("utf-8")).hexdigest()

    @classmethod
    def get_external_id(cls, info: FileInfo) -> str | None:
        file_hash = cls.get_hash(info)
        if file_hash is None:
            return
        return f"{info.product['id']}:{file_hash}"


OBJECTIVE = {
    # Essential keys for functioning of the system
    "@": get_file_info,
    "state": PublinovaFileExtraction.get_product_state,
    "set": lambda info: "publinova:publinova",
    "external_id": PublinovaFileExtraction.get_external_id,
    # Generic metadata
    "url": PublinovaFileExtraction.get_url,
    "hash": PublinovaFileExtraction.get_hash,
    "mime_type": lambda info: info.file["mime_type"] if info.file is not None else None,
    "title": lambda info: info.file["title"] if info.file is not None else None,
    "access_rights": lambda info: "OpenAccess",
    "product_id": lambda info: info.product["id"],
    "is_link": lambda info: False,
    "provider": lambda info: "publinova",
}


SEEDING_PHASES = [
    {
        "phase": "files",
        "strategy": "initial",
        "batch_size": 25,
        "retrieve_data": {
            "resource": "sources.publinovametadataresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE,
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


WEBHOOK_DATA_TRANSFORMER = PublinovaExtractor.webhook_data_transformer
