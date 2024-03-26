from typing import Iterator
from dataclasses import dataclass
import re
from hashlib import sha1

from django.conf import settings

from sources.utils.base import BaseExtractor


@dataclass(frozen=True, slots=True)
class ElectronicVersionInfo:
    is_link: bool
    data: dict
    access_info: dict
    product: dict


def get_electronic_version_info(pure_data: dict) -> Iterator[ElectronicVersionInfo]:
    for product in pure_data["items"]:
        electronic_versions = product.get("electronicVersions", []) + product.get("additionalFiles", [])
        if not electronic_versions:
            continue
        for electronic_version in electronic_versions:
            if "file" in electronic_version:
                is_link = False
                data = electronic_version["file"]
            elif "link" in electronic_version:
                is_link = True
                data = {"url": electronic_version["link"]}
            else:
                continue
            yield ElectronicVersionInfo(
                is_link=is_link,
                data=data,
                access_info=electronic_version.get("accessType", {}) or {},
                product=product,
            )


class HvaMetadataExtraction(BaseExtractor):

    youtube_regex = re.compile(r".*(youtube\.com|youtu\.be).*", re.IGNORECASE)

    @classmethod
    def get_record_state(cls, node):
        return "active"

    #############################
    # GENERIC
    #############################

    @staticmethod
    def _parse_file_url(url):
        file_path_segment = "/ws/api/"
        if file_path_segment not in url:
            return url  # not dealing with a url we recognize as a file url
        start = url.index(file_path_segment)
        file_path = url[start + len(file_path_segment):]
        return f"{settings.SOURCES_MIDDLEWARE_API}files/hva/{file_path}"

    @classmethod
    def get_url(cls, info: ElectronicVersionInfo) -> str:
        normalized_url = cls.parse_url(info.data["url"])
        return cls._parse_file_url(normalized_url)

    @classmethod
    def get_hash(cls, info: ElectronicVersionInfo) -> str:
        url = cls.get_url(info)
        return sha1(url.encode("utf-8")).hexdigest()

    @classmethod
    def get_external_id(cls, info: ElectronicVersionInfo) -> str:
        file_hash = cls.get_hash(info)
        return f"{info.product['uuid']}:{file_hash}"

    @classmethod
    def get_mime_type(cls, info: ElectronicVersionInfo) -> str:
        return info.data["mimeType"] if not info.is_link else "text/html"

    @classmethod
    def get_title(cls, info: ElectronicVersionInfo) -> str | None:
        return info.data.get("fileName")

    @classmethod
    def get_access_rights(cls, info: ElectronicVersionInfo) -> str:
        access_rights = "ClosedAccess"
        if info.access_info.get("uri", "").endswith("/open"):
            access_rights = "OpenAccess"
        elif info.access_info.get("uri", "").endswith("/restricted"):
            access_rights = "RestrictedAccess"
        return access_rights


OBJECTIVE = {
    # Essential keys for functioning of the system
    "@": get_electronic_version_info,
    "set": lambda info: "hva:hva",
    "external_id": HvaMetadataExtraction.get_external_id,
    # Generic metadata
    "url": HvaMetadataExtraction.get_url,
    "hash": HvaMetadataExtraction.get_hash,
    "mime_type": HvaMetadataExtraction.get_mime_type,
    "title": HvaMetadataExtraction.get_title,
    "access_rights": HvaMetadataExtraction.get_access_rights,
    "product_id": lambda info: info.product["uuid"],
    "is_link": lambda info: info.is_link,
    "provider": lambda info: "hva",
}


SEEDING_PHASES = [
    {
        "phase": "publications",
        "strategy": "initial",
        "batch_size": 100,
        "retrieve_data": {
            "resource": "sources.hvapureresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
