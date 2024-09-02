from typing import Iterator
from dataclasses import dataclass
from hashlib import sha1

from sources.utils.hku import HkuExtractor


FILE_TYPE_TO_MIME_TYPE = {
    "TEXT": "application/pdf",
    "VIDEO": "video/mp4",
    "AUDIO": "audio/mp3",
    "IMAGE": "image/jpeg",
    "NOT_SET": None
}


@dataclass(frozen=True, slots=True)
class FileInfo:
    data: dict
    product: dict


def get_file_info(hku_data: dict) -> Iterator[FileInfo]:
    for product in hku_data["root"]["item"]:
        document = product.get("document", {})
        file_info = document.get("file")
        if not file_info:
            continue
        yield FileInfo(data=file_info, product=product)


class HkuFileExtraction(HkuExtractor):

    @classmethod
    def get_external_id(cls, file_info: FileInfo) -> str:
        product_id = super().get_external_id(file_info.product)
        file_hash = cls.get_hash(file_info)
        return f"{product_id}:{file_hash}"

    @classmethod
    def get_language(cls, file_info: FileInfo):
        language = file_info.product["language"]
        if language == "Nederlands":
            return "nl"
        elif language == "Engels":
            return "en"
        return "unk"

    @classmethod
    def get_url(cls, file_info: FileInfo) -> str:
        return file_info.data["raw"].strip()

    @classmethod
    def get_hash(cls, file_info: FileInfo) -> str:
        url = cls.get_url(file_info)
        return sha1(url.encode("utf-8")).hexdigest()

    @classmethod
    def get_mime_type(cls, file_info: FileInfo) -> str:
        return FILE_TYPE_TO_MIME_TYPE.get(file_info.data["type"])

    @classmethod
    def get_title(cls, file_info: FileInfo) -> str:
        return file_info.data["title"]

    @classmethod
    def get_product_id(cls, file_info: FileInfo) -> str:
        return super().get_external_id(file_info.product)


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": get_file_info,
    "external_id": HkuFileExtraction.get_external_id,
    "set": lambda node: "hku:hku",
    "language": HkuFileExtraction.get_language,
    # Generic metadata
    "url": HkuFileExtraction.get_url,
    "hash": HkuFileExtraction.get_hash,
    "mime_type": HkuFileExtraction.get_mime_type,
    "title": HkuFileExtraction.get_title,
    "access_rights": lambda info: "OpenAccess",  # as agreed upon with an email by Emile Bijk on 1 December 2022
    "product_id": HkuFileExtraction.get_product_id,
    "is_link": lambda info: False,
    "provider": HkuFileExtraction.get_provider,
}

SEEDING_PHASES = [
    {
        "phase": "items",
        "strategy": "initial",
        "batch_size": 100,
        "retrieve_data": {
            "resource": "sources.hkumetadataresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
