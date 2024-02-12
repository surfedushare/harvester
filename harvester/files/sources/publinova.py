from typing import Iterator
from dataclasses import dataclass
from hashlib import sha1

from sources.utils.publinova import PublinovaExtractor


@dataclass(frozen=True, slots=True)
class FileInfo:
    file: dict
    product: dict


def get_file_info(publinova_data: dict) -> Iterator[FileInfo]:
    for product in publinova_data["data"]:
        files = product.get("files", [])
        if not files:
            continue
        for file_object in files:
            yield FileInfo(
                file=file_object,
                product=product,
            )


class PublinovaFileExtraction(PublinovaExtractor):

    @classmethod
    def get_record_state(cls, node):
        return "active"

    #############################
    # GENERIC
    #############################

    @classmethod
    def get_url(cls, info: FileInfo) -> str:
        return cls.parse_url(info.file["url"])

    @classmethod
    def get_hash(cls, info: FileInfo) -> str:
        url = cls.get_url(info)
        return sha1(url.encode("utf-8")).hexdigest()

    @classmethod
    def get_external_id(cls, info: FileInfo) -> str:
        file_hash = cls.get_hash(info)
        return f"{info.product['id']}:{file_hash}"

    @classmethod
    def get_mime_type(cls, info: FileInfo) -> str:
        return info.file["mime_type"]

    @classmethod
    def get_title(cls, info: FileInfo) -> str | None:
        return info.file["title"]


OBJECTIVE = {
    # Essential keys for functioning of the system
    "@": get_file_info,
    "set": lambda info: "publinova:publinova",
    "external_id": PublinovaFileExtraction.get_external_id,
    # Generic metadata
    "url": PublinovaFileExtraction.get_url,
    "hash": PublinovaFileExtraction.get_hash,
    "mime_type": lambda info: info.file["mime_type"],
    "title": lambda info: info.file["title"],
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
    }
]
