import os
from typing import Iterator, Type
from dataclasses import dataclass
from hashlib import sha1

from sources.utils.pure import PureExtractor


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


class PureFileExtraction(PureExtractor):

    file_url_property = "url"

    @classmethod
    def get_url(cls, info: ElectronicVersionInfo) -> str:
        url_property = "url" if info.is_link else cls.file_url_property
        normalized_url = cls.parse_url(info.data[url_property])
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
    def get_language(cls, info: ElectronicVersionInfo):
        locale_uri = info.product["language"]["uri"]
        _, locale = os.path.split(locale_uri)
        if locale in ["en_GB", "nl_NL"]:
            return locale[:2]
        return

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

    @classmethod
    def get_provider(cls, info: ElectronicVersionInfo):
        return super().get_provider(info.product)


def build_objective(extract_processor: Type[PureFileExtraction], source_set: str) -> dict:
    provider, set_name = source_set.split(":")
    return {
        # Essential keys for functioning of the system
        "@": get_electronic_version_info,
        "state": lambda node: "active",
        "set": lambda info: source_set,
        "external_id": extract_processor.get_external_id,
        "language": extract_processor.get_language,
        # Generic metadata
        "url": extract_processor.get_url,
        "hash": extract_processor.get_hash,
        "mime_type": extract_processor.get_mime_type,
        "title": extract_processor.get_title,
        "access_rights": extract_processor.get_access_rights,
        "product_id": lambda info: info.product["uuid"],
        "is_link": lambda info: info.is_link,
        "provider": extract_processor.get_provider,
    }
