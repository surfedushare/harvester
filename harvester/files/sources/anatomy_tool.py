import re
from mimetypes import guess_type
from hashlib import sha1
from collections import namedtuple
from typing import Iterator

import bs4
from django.utils.text import slugify

from sources.utils.base import BaseExtractor


FileInfo = namedtuple("FileInfo", ["product", "mime_type", "url"])


def get_file_infos(anatomy_tool_soup: bs4.BeautifulSoup) -> Iterator[FileInfo]:
    for product in anatomy_tool_soup.find_all('record'):
        mime_types = product.find_all('format')
        urls = product.find_all('location')
        if not urls:  # anything without a URL will get deleted
            continue
        for mime_type, url in zip(mime_types, urls):
            yield FileInfo(product, mime_type, url)


class AnatomyToolFileExtraction(BaseExtractor):

    youtube_regex = re.compile(r".*(youtube\.com|youtu\.be).*", re.IGNORECASE)
    cc_url_regex = re.compile(r"^https?://creativecommons\.org/(?P<type>\w+)/(?P<license>[a-z\-]+)/(?P<version>\d\.\d)",
                              re.IGNORECASE)
    cc_code_regex = re.compile(r"^cc([ \-][a-z]{2})+$", re.IGNORECASE)

    #############################
    # OAI-PMH
    #############################

    @classmethod
    def parse_copyright_description(cls, description: None | str) -> None | str:
        if description is None:
            return
        elif description == "Public Domain":
            return "pdm-10"
        elif description == "Copyrighted":
            return "yes"
        url_match = cls.cc_url_regex.match(description)
        if url_match is None:
            code_match = cls.cc_code_regex.match(description)
            return slugify(description.lower()) if code_match else None
        license = url_match.group("license").lower()
        if license == "mark":
            license = "pdm"
        elif license == "zero":
            license = "cc0"
        else:
            license = "cc-" + license
        return slugify(f"{license}-{url_match.group('version')}")

    @classmethod
    def get_set(cls, soup: bs4.BeautifulSoup, file_info: FileInfo) -> str:
        return "anatomy_tool:anatomy_tool"

    #############################
    # GENERIC
    #############################

    @staticmethod
    def find_all_classification_blocks(element: bs4.element.Tag, classification_type: str, output_type: str)\
            -> list[bs4.element.Tag]:
        assert output_type in ["entry", "id"]
        entries = element.find_all(string=classification_type)
        blocks = []
        for entry in entries:
            classification_element = entry.find_parent('classification')
            if not classification_element:
                continue
            blocks += classification_element.find_all(output_type)
        return blocks

    @classmethod
    def get_url(cls, soup: bs4.BeautifulSoup, file_info: FileInfo) -> str:
        return cls.parse_url(file_info.url.text)

    @classmethod
    def get_hash(cls, soup: bs4.BeautifulSoup, file_info: FileInfo) -> str:
        url = cls.get_url(soup, file_info)
        return sha1(url.encode("utf-8")).hexdigest()

    @classmethod
    def get_product_id(cls, soup: bs4.BeautifulSoup, file_info: FileInfo) -> str:
        return file_info.product.find('identifier').text.strip()

    @classmethod
    def get_external_id(cls, soup: bs4.BeautifulSoup, file_info: FileInfo) -> str:
        file_hash = cls.get_hash(soup, file_info)
        product_id = cls.get_product_id(soup, file_info)
        return f"{product_id}:{file_hash}"

    @classmethod
    def get_title(cls, soup: bs4.BeautifulSoup, file_info: FileInfo) -> str | None:
        el = file_info.product
        node = el.find('title')
        if node is None:
            return
        translation = node.find('string')
        return translation.text.strip() if translation else None

    @classmethod
    def get_mime_type(cls, soup: bs4.BeautifulSoup, file_info: FileInfo) -> str | None:
        el = file_info.product
        node = el.find('format')
        if node:
            return node.text.strip()
        url = cls.get_url(soup, file_info)
        if not url:
            return
        mime_type, encoding = guess_type(url)
        return mime_type

    @classmethod
    def get_is_link(cls, soup: bs4.BeautifulSoup, file_info: FileInfo) -> bool:
        return file_info.mime_type.text.strip() == "text/html"

    @classmethod
    def get_copyright(cls, soup: bs4.BeautifulSoup, file_info: FileInfo) -> str:
        return cls.parse_copyright_description(cls.get_copyright_description(soup, file_info)) or "yes"

    @classmethod
    def get_provider(cls, soup: bs4.BeautifulSoup, file_info: FileInfo) -> dict[str, None | str]:
        return {
            "ror": None,
            "external_id": None,
            "slug": "anatomy_tool",
            "name": "AnatomyTOOL"
        }

    @classmethod
    def get_access_rights(cls, soup: bs4.BeautifulSoup, file_info: FileInfo) -> None | str:
        default_copyright = cls.get_copyright(soup, file_info)
        return "OpenAccess" if default_copyright != "yes" else "RestrictedAccess"

    @classmethod
    def get_copyright_description(cls, soup: bs4.BeautifulSoup, file_info: FileInfo) -> None | str:
        el = file_info.product
        node = el.find('rights')
        if not node:
            return
        description = node.find('description')
        return description.find('string').text.strip() if description else None


OBJECTIVE = {
    "@": get_file_infos,
    "external_id": AnatomyToolFileExtraction.get_external_id,
    "set": AnatomyToolFileExtraction.get_set,
    "url": AnatomyToolFileExtraction.get_url,
    "hash": AnatomyToolFileExtraction.get_hash,
    "title": AnatomyToolFileExtraction.get_title,
    "mime_type": AnatomyToolFileExtraction.get_mime_type,
    "is_link": AnatomyToolFileExtraction.get_is_link,
    "copyright": AnatomyToolFileExtraction.get_copyright,
    "access_rights": AnatomyToolFileExtraction.get_access_rights,
    "provider": AnatomyToolFileExtraction.get_provider,
    "product_id": AnatomyToolFileExtraction.get_product_id,
}


SEEDING_PHASES = [
    {
        "phase": "publications",
        "strategy": "initial",
        "batch_size": 25,
        "retrieve_data": {
            "resource": "sources.anatomytooloaipmh",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
