from typing import Type
import vobject
from hashlib import sha1
from datetime import datetime
from dateutil.parser import ParserError, parse as date_parser

from sources.utils.hbo_kennisbank import HBOKennisbankExtractor


class HBOKennisbankProductExtractor(HBOKennisbankExtractor):

    language_mapping = {
        "nl": "nl",
        "en": "en",
        "dut": "nl",
        "eng": "en"
    }

    #############################
    # OAI-PMH
    #############################

    @staticmethod
    def parse_vcard_element(el):
        card = "\n".join(field.strip() for field in el.text.strip().split("\n"))
        return vobject.readOne(card)

    #############################
    # HELPERS
    #############################

    @classmethod
    def _extract_url(cls, resource):
        item = next((parent for parent in resource.parents if parent.name == "Item"), None)
        if not item:
            return
        element = item.find("Resource")
        if not element:
            return
        return cls.parse_url(element["ref"])

    #############################
    # EXTRACTION
    #############################

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


def build_objective(extract_processor: Type[HBOKennisbankProductExtractor]) -> dict:
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
        "copyright": extract_processor.get_copyright,
        "copyright_description": extract_processor.get_copyright_description,
        "authors": extract_processor.get_authors,
        "publishers": extract_processor.get_publishers,
        "publisher_date": extract_processor.get_publisher_date,
        "publisher_year": extract_processor.get_publisher_year,
        "organizations": extract_processor.get_organizations,
        "research_product.research_object_type": extract_processor.get_research_object_type,
    }
