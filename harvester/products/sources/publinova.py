from datetime import datetime
from dateutil.parser import parse as date_parser
from sentry_sdk import capture_message

from sources.utils.publinova import PublinovaExtractor


class PublinovaProductExtraction(PublinovaExtractor):

    @classmethod
    def get_record_state(cls, node):
        return node.get("state", "active")

    #############################
    # GENERIC
    #############################

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
            return
        capture_message(f"Received a language from Publinova: {language}", level="warning")
        return language

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
            author["is_external"] = None
            author.pop("about", None)
        return authors

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
    "state": PublinovaProductExtraction.get_record_state,
    "set": lambda node: "publinova:publinova",
    "external_id": "$.id",
    # Generic metadata
    "modified_at": "$.modified_at",
    "files": PublinovaProductExtraction.get_files,
    "title": "$.title",
    "language": PublinovaProductExtraction.get_language,
    "keywords": PublinovaProductExtraction.get_keywords,
    "description": "$.description",
    "copyright": PublinovaProductExtraction.get_copyright,
    "authors": PublinovaProductExtraction.get_authors,
    "provider": PublinovaProductExtraction.get_provider,
    "organizations": PublinovaProductExtraction.get_organizations,
    "publishers": PublinovaProductExtraction.get_publishers,
    "publisher_date": PublinovaProductExtraction.get_publisher_date,
    "publisher_year": PublinovaProductExtraction.get_publisher_year,
    "doi": PublinovaProductExtraction.get_doi,
    # Research product metadata
    "research_product.research_object_type": "$.research_object_type",
    "research_product.research_themes": PublinovaProductExtraction.get_research_themes,
}


SEEDING_PHASES = [
    {
        "phase": "products",
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


WEBHOOK_DATA_TRANSFORMER = PublinovaExtractor.webhook_data_transformer
