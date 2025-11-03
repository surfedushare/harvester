from typing import Iterator, Type

import bs4

from sources.utils.hbo_kennisbank import build_seeding_phases
from sources.models import GreeniOAIPMHResource
from files.sources.hbo_kennisbank import (
    FileInfo,
    HBOKennisbankFileExtractor,
    back_fill_deletes,
)


class GreeniFileExtractor(HBOKennisbankFileExtractor):
    source_slug = "greeni"

    @classmethod
    def get_oaipmh_set(cls, soup):
        oaipmh_set = super().get_oaipmh_set(soup)
        if oaipmh_set:
            return oaipmh_set
        request = soup.find("request")
        resumption_token = request.get("resumptionToken", "").strip()
        set_specification = resumption_token.split("|")[0]
        if not set_specification:
            return
        return f"{cls.source_slug}:{set_specification}"


def get_file_infos(hbo_kennisbank_soup: bs4.BeautifulSoup) -> Iterator[FileInfo]:
    for product in GreeniFileExtractor.get_oaipmh_records(hbo_kennisbank_soup):
        found_files = False
        # Handle files
        file_resources = GreeniFileExtractor.find_resources(product, "file")
        link_resources = GreeniFileExtractor.find_resources(product, "link")
        if not file_resources and not link_resources:
            yield FileInfo(product, None, None, False)
        for file_resource in file_resources:
            file_item = next(
                (parent for parent in file_resource.parents if parent.name == "Item"),
                None,
            )
            if not file_item:
                yield FileInfo(product, None, None, False)
            file_element = file_item.find("Resource")
            yield FileInfo(product, file_element, file_item, False)
            found_files = True

        if not found_files:
            # Handle links
            for link_resource in link_resources:
                link_item = next(
                    (
                        parent
                        for parent in link_resource.parents
                        if parent.name == "Item"
                    ),
                    None,
                )
                if not link_item:
                    yield FileInfo(product, None, None, True)
                link_element = link_item.find("Resource")
                yield FileInfo(product, link_element, link_item, True)


def build_objective(extract_processor: Type[GreeniFileExtractor]) -> dict:
    return {
        # Essential objective keys for system functioning
        "@": get_file_infos,
        "state": extract_processor.get_oaipmh_record_state,
        "external_id": extract_processor.get_external_id,
        "language": extract_processor.get_language,
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


OBJECTIVE = build_objective(GreeniFileExtractor)


SEEDING_PHASES = build_seeding_phases(
    GreeniOAIPMHResource, OBJECTIVE, back_fill_deletes=back_fill_deletes
)
