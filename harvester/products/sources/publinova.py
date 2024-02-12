import re
from datetime import datetime
from hashlib import sha1
from dateutil.parser import parse as date_parser
from sentry_sdk import capture_message

from sources.utils.base import BaseExtractor


class PublinovaMetadataExtraction(BaseExtractor):

    @classmethod
    def get_record_state(cls, node):
        return node.get("state", "active")

    #############################
    # GENERIC
    #############################

    @staticmethod
    def _parse_file(file_object):
        url = file_object["url"]
        file_object["hash"] = sha1(url.encode("utf-8")).hexdigest()
        file_object["copyright"] = None
        file_object["access_rights"] = "OpenAccess"
        return file_object

    @classmethod
    def get_files(cls, node):
        return [
            cls.parse_url(file_object["url"])
            for file_object in node.get("files", [])
        ]

    @classmethod
    def get_language(cls, node):
        language = node.get("language", None)
        if not language:
            return "unk"
        capture_message(f"Received a language from Publinova: {language}", level="warning")
        return "unk"

    @classmethod
    def get_copyright(cls, node):
        return node.get("copyright", None)

    @classmethod
    def get_keywords(cls, node):
        return [
            keyword["label"] for keyword in node.get("keywords", [])
        ]

    @classmethod
    def get_authors(cls, node):
        authors = node.get("authors", [])
        for author in authors:
            external_id = author.pop("id")
            author["external_id"] = external_id
            author.pop("about", None)
        return authors

    @classmethod
    def get_provider(cls, node):
        return {
            "ror": None,
            "external_id": None,
            "slug": "publinova",
            "name": "Publinova"
        }

    @classmethod
    def get_organizations(cls, node):
        root = cls.get_provider(node)
        root["type"] = "repository"
        return {
            "root": root,
            "departments": [],
            "associates": []
        }

    @classmethod
    def get_publisher_year(cls, node):
        published_at = node.get("published_at", None)
        if published_at is None:
            return
        date = date_parser(published_at)
        return date.year

    @classmethod
    def get_publisher_date(cls, node):
        published_at = node.get("published_at", None)
        if published_at is None:
            return
        date = date_parser(published_at, default=datetime(year=1970, month=1, day=1))
        return date.strftime('%Y-%m-%d')

    @classmethod
    def get_research_themes(cls, node):
        return [theme["label"] for theme in node.get("research_themes", None) or []]

    @classmethod
    def get_publishers(cls, node):
        return [party["name"] for party in node.get("parties", []) or []]

    @classmethod
    def get_doi(cls, node):
        doi = node.get("doi", None)
        if not doi:
            return
        try:
            return "10." + doi.split("10.", 1)[1].replace(" ", "+")
        except IndexError:
            return None


OBJECTIVE = {
    # Essential keys for functioning of the system
    "@": "$.data",
    "state": PublinovaMetadataExtraction.get_record_state,
    "set": lambda node: "publinova:publinova",
    "external_id": "$.id",
    # Generic metadata
    "files": PublinovaMetadataExtraction.get_files,
    "title": "$.title",
    "language": PublinovaMetadataExtraction.get_language,
    "keywords": PublinovaMetadataExtraction.get_keywords,
    "description": "$.description",
    "copyright": PublinovaMetadataExtraction.get_copyright,
    "authors": PublinovaMetadataExtraction.get_authors,
    "provider": PublinovaMetadataExtraction.get_provider,
    "organizations": PublinovaMetadataExtraction.get_organizations,
    "publishers": PublinovaMetadataExtraction.get_publishers,
    "publisher_date": PublinovaMetadataExtraction.get_publisher_date,
    "publisher_year": PublinovaMetadataExtraction.get_publisher_year,
    "doi": PublinovaMetadataExtraction.get_doi,
    # Research product metadata
    "research_product.research_object_type": "$.research_object_type",
    "research_product.research_themes": PublinovaMetadataExtraction.get_research_themes,
}


SEEDING_PHASES = [
    {
        "phase": "publications",
        "strategy": "initial",
        "batch_size": 25,
        "retrieve_data": {
            "resource": "sources.publinovametadataresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE,
        }
    }
]
