from typing import Type
import re
import bs4
import vobject
from hashlib import sha1
from datetime import datetime
from dateutil.parser import ParserError, parse as date_parser

from django.utils.text import slugify

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
    }
}


class HBOKennisbankExtractor(BaseExtractor):

    source_slug = None

    cc_url_regex = re.compile(r"^https?://creativecommons\.org/(?P<type>\w+)/(?P<license>[a-z\-]+)/(?P<version>\d\.\d)",
                              re.IGNORECASE)
    cc_code_regex = re.compile(r"^cc([ \-][a-z]{2})+$", re.IGNORECASE)

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
    def parse_copyright_description(cls, description):
        if description is None:
            return
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

    @staticmethod
    def parse_vcard_element(el):
        card = "\n".join(field.strip() for field in el.text.strip().split("\n"))
        return vobject.readOne(card)

    @classmethod
    def get_oaipmh_records(cls, soup):
        return soup.find_all('record')

    @classmethod
    def get_oaipmh_set(cls, soup):
        request = soup.find("request")
        set_specification = request.get("set", "").strip()
        if not set_specification:
            return
        return f"{cls.source_slug}:{set_specification}"

    @classmethod
    def get_oaipmh_external_id(cls, soup, el):
        return el.find('identifier').text.strip()

    @classmethod
    def get_oaipmh_record_state(cls, soup, el):
        header = el.find('header')
        return header.get("status", "active")

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

    @classmethod
    def find_metadata(cls, xml) -> bs4.Tag | None:
        resources = cls.find_resources(xml, "meta")
        if not resources:
            return
        elif len(resources) > 1:
            raise AssertionError(f"Unexpected length for metadata resource: {len(resources)}")
        metadata = resources[0]
        item = next((parent for parent in metadata.parents if parent.name == "Item"), None)
        if not item:
            raise AssertionError("Metadata descriptor did not have an item as parent")
        return item.find("Resource")

    @classmethod
    def _extract_url(cls, resource):
        item = next((parent for parent in resource.parents if parent.name == "Item"), None)
        if not item:
            print("not item")
            return
        element = item.find("Resource")
        if not element:
            print("not element")
            return
        return cls.parse_url(element["ref"])

    #############################
    # EXTRACTION
    #############################

    @classmethod
    def get_provider(cls, soup, el):
        set_specification = cls.get_oaipmh_set(soup)
        return HBO_KENNISBANK_SET_TO_PROVIDER[set_specification]

    @classmethod
    def get_files(cls, soup, el):
        file_resources = cls.find_resources(el, "file")
        link_resources = cls.find_resources(el, "link")
        resources = file_resources + link_resources
        urls = []
        for resource in resources:
            url = cls._extract_url(resource)
            if url:
                urls.append(url)
        return urls

    @classmethod
    def get_language(cls, soup, el):
        language_term = el.find("languageTerm")
        if not language_term:
            return "unk"
        return cls.language_mapping[language_term.text.strip()]

    @classmethod
    def get_title(cls, soup, el):
        node = el.find('title')
        return node.text.strip() if node else None

    @classmethod
    def get_description(cls, soup, el):
        node = el.find('abstract')
        return node.text if node else None

    @classmethod
    def get_authors(cls, soup, el):
        roles = el.find_all(string='aut')
        if not roles:
            return []
        authors = []
        for role in roles:
            author = role.find_parent('name')
            if not author:
                continue
            given_name = author.find('namePart', attrs={"type": "given"})
            family_name = author.find('namePart', attrs={"type": "family"})
            if not given_name and not family_name:
                continue
            elif not given_name:
                name = family_name.text.strip()
            elif not family_name:
                name = given_name.text.strip()
            else:
                name = f"{given_name.text.strip()} {family_name.text.strip()}"
            authors.append({
                "name": name,
                "email": None,
                "external_id":
                    cls.get_provider(soup, el)["slug"] +
                    ":person:" + sha1(name.encode('utf-8')).hexdigest(),
                "dai": None,
                "orcid": None,
                "isni": None,
            })
        return authors

    @classmethod
    def get_publishers(cls, soup, el):
        publisher = el.find("publisher")
        return [publisher.text.strip()] if publisher else []

    @classmethod
    def get_publisher_date(cls, soup, el):
        date_issued = el.find("dateIssued")
        if not date_issued:
            return
        date_str = date_issued.text.strip().strip("[]")
        default_datetime = datetime(year=1970, month=1, day=1)
        return date_parser(date_str, default=default_datetime).strftime("%Y-%m-%d")

    @classmethod
    def get_publisher_year(cls, soup, el):
        date_issued = el.find("dateIssued")
        if not date_issued:
            return
        publication_datetime = None
        try:
            publication_datetime = date_parser(date_issued.text)
        except ParserError:
            pass
        return publication_datetime.year if publication_datetime else None

    @classmethod
    def get_organizations(cls, soup, el):
        provider = cls.get_provider(soup, el)
        return {
            "root": provider,
            "departments": [],
            "associates": []
        }

    @classmethod
    def get_research_object_type(cls, soup, el):
        genre = el.find("genre")
        return genre.text.strip() if genre else None

    @classmethod
    def get_doi(cls, soup, el):
        identifier = el.find("identifier", attrs={"type": "doi"})
        if not identifier:
            identifier = el.find("identifier", attrs={"type": "uri"})
        if not identifier:
            return None
        try:
            return "10." + identifier.text.strip().split("10.", 1)[1].replace(" ", "+")
        except IndexError:
            return None


def build_objective(extract_processor: Type[HBOKennisbankExtractor]) -> dict:
    return {
        # Essential objective keys for system functioning
        "@": extract_processor.get_oaipmh_records,
        "state": extract_processor.get_oaipmh_record_state,
        "external_id": extract_processor.get_oaipmh_external_id,
        "#set": extract_processor.get_oaipmh_set,
        # Generic metadata
        "provider": extract_processor.get_provider,
        "doi": extract_processor.get_doi,
        "files": extract_processor.get_files,
        "language": extract_processor.get_language,
        "title": extract_processor.get_title,
        "description": extract_processor.get_description,
        "authors": extract_processor.get_authors,
        "publishers": extract_processor.get_publishers,
        "publisher_date": extract_processor.get_publisher_date,
        "publisher_year": extract_processor.get_publisher_year,
        "organizations": extract_processor.get_organizations,
        "research_product.research_object_type": extract_processor.get_research_object_type,
    }


def build_seeding_phases(resource: Type[HttpResource], objective: dict) -> list[dict]:
    resource_label = f"{resource._meta.app_label}.{resource._meta.model_name}"
    return [
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
