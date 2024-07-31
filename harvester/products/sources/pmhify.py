import bs4
from dateutil.parser import parse as date_parser

from sources.utils.base import BaseExtractor


class PmhifyExtraction(BaseExtractor):

    #############################
    # OAI-PMH
    #############################

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

    @classmethod
    def get_oaipmh_modified_at(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> str:
        header = el.find("header")
        return header.find("datestamp").text.strip()

    #############################
    # GENERIC
    #############################

    @classmethod
    def get_files(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> list[str]:
        return [cls.parse_url(url.text) for url in el.find_all('location')]

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
    def get_description(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> None | str:
        node = el.find('description')
        if node is None:
            return
        translation = node.find('string')
        return translation.text if translation else None

    @classmethod
    def get_copyright(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag):
        node = el.find('copyrightandotherrestrictions')
        if node is None:
            return "yes"
        copyright_ = node.find('czp:value').find('czp:langstring').text.strip()
        return copyright_ or "yes"

    @classmethod
    def get_provider(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> dict[str, None | str]:
        return {
            "ror": None,
            "external_id": None,
            "slug": "pmhify",
            "name": "PMHify ... probably incorrect?"
        }

    @classmethod
    def get_organizations(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> dict[str, list | dict[str, None | str]]:
        root = cls.get_provider(soup, el)
        return {
            "root": root,
            "departments": [],
            "associates": []
        }

    @classmethod
    def get_publishers(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> list[str]:
        return ["PMHify ... probably incorrect?"]

    @classmethod
    def get_publisher_date(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> None | str:
        publisher = el.find(string='Publicatie datum')
        if not publisher:
            return
        date = publisher.find_parent('date')
        if not date:
            return
        datetime = date.find('dateTime')
        if not datetime or not datetime.text:
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


OBJECTIVE = {
    "@": PmhifyExtraction.get_oaipmh_records,
    "external_id": PmhifyExtraction.get_oaipmh_external_id,
    "set": lambda soup, el: "mediasite:mediasite",
    "state": PmhifyExtraction.get_oaipmh_record_state,
    "modified_at": PmhifyExtraction.get_oaipmh_modified_at,
    "language": PmhifyExtraction.get_language,
    "files": PmhifyExtraction.get_files,
    "title": PmhifyExtraction.get_title,
    "description": PmhifyExtraction.get_description,
    "copyright": PmhifyExtraction.get_copyright,
    "provider": PmhifyExtraction.get_provider,
    "organizations": PmhifyExtraction.get_organizations,
    "publishers": PmhifyExtraction.get_publishers,
    "publisher_date": PmhifyExtraction.get_publisher_date,
    "publisher_year": PmhifyExtraction.get_publisher_year,
}

SEEDING_PHASES = [
    {
        "phase": "publications",
        "strategy": "initial",
        "batch_size": 25,
        "retrieve_data": {
            "resource": "sources.pmhifyoaipmhresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE,
        }
    }
]
