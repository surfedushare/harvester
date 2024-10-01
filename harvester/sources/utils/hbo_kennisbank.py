from typing import Type, Callable, Optional
import bs4

from datagrowth.resources import HttpResource
from sources.utils.base import BaseExtractor


HBO_KENNISBANK_SET_TO_PROVIDER = {
    "greeni:PUBVHL": {
        "ror": None,
        "external_id": None,
        "slug": "PUBVHL",
        "name": "Hogeschool Van Hall Larenstein"
    },
    "saxion:kenniscentra": {
        "ror": None,
        "external_id": None,
        "slug": "saxion",
        "name": "Saxion"
    },
    "greeni:PUBHAS": {
        "ror": None,
        "external_id": None,
        "slug": "PUBHAS",
        "name": "HAS Green Academy"
    }
}


class HBOKennisbankExtractor(BaseExtractor):

    source_slug = None

    language_mapping = {
        "nl": "nl",
        "en": "en",
        "dut": "nl",
        "eng": "en"
    }

    #############################
    # OAI-PMH
    #############################

    @classmethod
    def get_oaipmh_records(cls, soup):
        return soup.find_all('record')

    @classmethod
    def get_oaipmh_record_state(cls, soup, el):
        header = el.find('header')
        return header.get("status", "active")

    @classmethod
    def get_oaipmh_external_id(cls, soup, el):
        return el.find('identifier').text.strip()

    @classmethod
    def get_oaipmh_modified_at(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> str:
        header = el.find("header")
        return header.find("datestamp").text.strip()

    @classmethod
    def get_oaipmh_set(cls, soup):
        request = soup.find("request")
        set_specification = request.get("set", "").strip()
        if not set_specification:
            return
        return f"{cls.source_slug}:{set_specification}"

    #############################
    # HELPERS
    #############################

    @classmethod
    def find_resources(cls, xml, resource_type) -> list[bs4.Tag]:
        resource_code = None
        if resource_type == "file":
            resource_code = "objectFile"
        elif resource_type == "link":
            resource_code = "humanStartPage"
        elif resource_type == "meta":
            resource_code = "descriptiveMetadata"
        resource_identifier = f"info:eu-repo/semantics/{resource_code}"
        return xml.find_all("rdf:type", attrs={"rdf:resource": resource_identifier})

    #############################
    # Extraction
    #############################

    @classmethod
    def get_product_language(cls, soup, record):
        language_term = record.find("languageTerm")
        if not language_term:
            return
        return cls.language_mapping.get(language_term.text.strip())

    @classmethod
    def get_provider(cls, soup, el):
        set_specification = cls.get_oaipmh_set(soup)
        return HBO_KENNISBANK_SET_TO_PROVIDER[set_specification]

    @classmethod
    def get_copyright(cls, soup, el):
        copyright_description = cls.get_copyright_description(soup, el)
        return cls.parse_copyright_description(copyright_description)

    @classmethod
    def get_copyright_description(cls, soup, el):
        copyright_desciption = el.find("rights")
        if not copyright_desciption:
            return
        return copyright_desciption.text.strip()


def build_seeding_phases(resource: Type[HttpResource], objective: dict,
                         back_fill_deletes: Optional[Callable] = None) -> list[dict]:
    resource_label = f"{resource._meta.app_label}.{resource._meta.model_name}"
    phases = [
        {
            "phase": "records",
            "strategy": "initial",
            "batch_size": 25,
            "retrieve_data": {
                "resource": resource_label,
                "method": "get",
                "args": [],
                "kwargs": {},
            },
            "contribute_data": {
                "objective": objective
            }
        }
    ]
    if back_fill_deletes:
        phases.append({
            "phase": "deletes",
            "strategy": "back_fill",
            "batch_size": 25,
            "contribute_data": {
                "callback": back_fill_deletes
            },
            "is_post_initialization": True
        })
    return phases
