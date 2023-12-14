import re

import bs4
import vobject
from dateutil.parser import parse as date_parser

from django.utils.text import slugify


class AnatomyToolExtraction(object):

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

    @staticmethod
    def parse_vcard_element(el: bs4.BeautifulSoup):
        card = "\n".join(field.strip() for field in el.text.strip().split("\n"))
        card = card.replace("BEGIN:VCARD - VERSION:3.0 -", "BEGIN:VCARD\nVERSION:3.0")
        return vobject.readOne(card)

    @classmethod
    def get_oaipmh_records(cls, soup: bs4.BeautifulSoup) -> list[bs4.element.Tag]:
        return soup.find_all('record')

    @classmethod
    def get_oaipmh_external_id(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> str:
        return el.find('identifier').text.strip()

    @classmethod
    def get_oaipmh_record_state(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> str:
        header = el.find('header')
        return header.get("status", "active")

    #############################
    # GENERIC
    #############################

    @classmethod
    def get_files(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> list[str]:
        return [url.text.strip() for url in el.find_all('location')]

    @classmethod
    def get_title(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> None | str:
        node = el.find('title')
        if node is None:
            return
        translation = node.find('string')
        return translation.text.strip() if translation else None

    @classmethod
    def get_language(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> None | str:
        node = el.find('language')
        return node.text.strip() if node else None

    @classmethod
    def get_keywords(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> list[str]:
        general = el.find('general')
        if not general:
            return []
        nodes = general.find_all('keyword')
        return [
            node.find('string').text.strip()
            for node in nodes if node.find('string').text
        ]

    @classmethod
    def get_description(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> None | str:
        node = el.find('description')
        if node is None:
            return
        translation = node.find('string')
        return translation.text if translation else None

    @classmethod
    def get_copyright(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> str:
        return cls.parse_copyright_description(cls.get_copyright_description(soup, el)) or "yes"

    @classmethod
    def get_aggregation_level(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> None | str:
        node = el.find('aggregationlevel', None)
        if node is None:
            return None
        return node.find('value').text.strip() if node else None

    @classmethod
    def get_authors(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> list[dict[str, None | str]]:
        lifecycle = el.find('lifecycle')
        if not lifecycle:
            return []
        nodes = lifecycle.find_all('entity')

        authors = []
        for node in nodes:
            author = cls.parse_vcard_element(node)
            if hasattr(author, "fn"):
                authors.append({
                    "name": author.fn.value.strip(),
                    "email": None,
                    "external_id": None,
                    "dai": None,
                    "orcid": None,
                    "isni": None,
                })
        return authors

    @classmethod
    def get_provider(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> dict[str, None | str]:
        return {
            "ror": None,
            "external_id": None,
            "slug": "anatomy_tool",
            "name": "AnatomyTOOL"
        }

    @classmethod
    def get_organizations(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> dict[str, list | dict[str, None | str]]:
        root = cls.get_provider(soup, el)
        root["type"] = "consortium"
        return {
            "root": root,
            "departments": [],
            "associates": []
        }

    @classmethod
    def get_publishers(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> list[str]:
        return ["AnatomyTOOL"]

    @classmethod
    def get_consortium(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> str:
        return "AnatomyTOOL"

    @classmethod
    def get_publisher_date(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> None | str:
        publisher = el.find(string='Created')
        if not publisher:
            return
        contribution = publisher.find_parent('contribute')
        if not contribution:
            return
        datetime = contribution.find('datetime')
        if not datetime:
            return
        datetime = date_parser(datetime.text)
        return datetime.strftime("%Y-%m-%d")

    @classmethod
    def get_publisher_year(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> None | int:
        publisher_date = cls.get_publisher_date(soup, el)
        if publisher_date is None:
            return
        datetime = date_parser(publisher_date)
        return datetime.year

    @classmethod
    def get_lom_educational_levels(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> list[str]:
        return ["HBO", "WO"]

    @classmethod
    def get_copyright_description(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> None | str:
        node = el.find('rights')
        if not node:
            return
        description = node.find('description')
        return description.find('string').text.strip() if description else None

    @classmethod
    def get_learning_material_disciplines(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> list[str]:
        return ["gezondheid"]

    @staticmethod
    def find_all_classification_blocks(element: bs4.element.Tag, classification_type: str, output_type: str) \
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
    def get_studies(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> list[str]:
        blocks = cls.find_all_classification_blocks(el, "discipline", "id")
        return list(set([block.text.strip() for block in blocks]))


OBJECTIVE = {
    "@": AnatomyToolExtraction.get_oaipmh_records,
    "external_id": AnatomyToolExtraction.get_oaipmh_external_id,
    "set": lambda soup, el: "anatomy_tool:anatomy_tool",
    "state": AnatomyToolExtraction.get_oaipmh_record_state,
    "files": AnatomyToolExtraction.get_files,
    "title": AnatomyToolExtraction.get_title,
    "language": AnatomyToolExtraction.get_language,
    "keywords": AnatomyToolExtraction.get_keywords,
    "description": AnatomyToolExtraction.get_description,
    "copyright": AnatomyToolExtraction.get_copyright,
    "authors": AnatomyToolExtraction.get_authors,
    "provider": AnatomyToolExtraction.get_provider,
    "organizations": AnatomyToolExtraction.get_organizations,
    "publishers": AnatomyToolExtraction.get_publishers,
    "publisher_date": AnatomyToolExtraction.get_publisher_date,
    "publisher_year": AnatomyToolExtraction.get_publisher_year,
    "copyright_description": AnatomyToolExtraction.get_copyright_description,
    # Learning material metadata
    "learning_material.aggregation_level": AnatomyToolExtraction.get_aggregation_level,
    "learning_material.lom_educational_levels": AnatomyToolExtraction.get_lom_educational_levels,
    "learning_material.disciplines": AnatomyToolExtraction.get_learning_material_disciplines,
    "learning_material.consortium": AnatomyToolExtraction.get_consortium,
    "learning_material.studies": AnatomyToolExtraction.get_studies,
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
            "objective": OBJECTIVE,
        }
    }
]
