import re
from mimetypes import guess_type
from hashlib import sha1
from dateutil.parser import parse as date_parser
from sentry_sdk import capture_message

from django.conf import settings

from datagrowth.processors import ExtractProcessor


class PublinovaMetadataExtraction(ExtractProcessor):

    youtube_regex = re.compile(r".*(youtube\.com|youtu\.be).*", re.IGNORECASE)

    @classmethod
    def get_record_state(cls, node):
        return "active"

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
            cls._parse_file(file_object)
            for file_object in node["files"]
        ]

    @classmethod
    def get_language(cls, node):
        language = node["language"]
        if not language:
            return "unk"
        capture_message(f"Received a language from Publinova: {language}", level="warning")
        return "unk"

    @classmethod
    def get_url(cls, node):
        files = cls.get_files(node)
        if not files:
            return
        return files[0]["url"].strip()

    @classmethod
    def get_mime_type(cls, node):
        files = cls.get_files(node)
        if not files:
            return
        return files[0]["mime_type"]

    @classmethod
    def get_technical_type(cls, node):
        files = cls.get_files(node)
        if not files:
            return
        technical_type = settings.MIME_TYPE_TO_TECHNICAL_TYPE.get(files[0]["mime_type"], None)
        if technical_type:
            return technical_type
        file_url = files[0]["url"]
        if not file_url:
            return
        mime_type, encoding = guess_type(file_url)
        return settings.MIME_TYPE_TO_TECHNICAL_TYPE.get(mime_type, "unknown")

    @classmethod
    def get_copyright(cls, node):
        return node["copyright"]

    @classmethod
    def get_keywords(cls, node):
        return [
            keyword["label"] for keyword in node["keywords"]
        ]

    @classmethod
    def get_from_youtube(cls, node):
        url = cls.get_url(node)
        if not url:
            return False
        return cls.youtube_regex.match(url) is not None

    @classmethod
    def get_authors(cls, node):
        authors = node["authors"]
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
    def get_publishers(cls, node):
        return ["Publinova"]

    @classmethod
    def get_publisher_year(cls, node):
        published_at = node["published_at"]
        if published_at is None:
            return
        datetime = date_parser(published_at)
        return datetime.year

    @classmethod
    def get_is_restricted(cls, node):
        return False

    @classmethod
    def get_analysis_allowed(cls, node):
        files = cls.get_files(node)
        if not len(files):
            return False
        match files[0]["access_rights"], files[0]["copyright"]:
            case "OpenAccess", _:
                return True
            case "RestrictedAccess", copyright:
                return copyright and copyright not in ["yes", "unknown"] and "nd" not in copyright
            case "ClosedAccess", _:
                return False

    @classmethod
    def get_research_themes(cls, node):
        return [theme["label"] for theme in node["research_themes"] or []]

    @classmethod
    def get_parties(cls, node):
        return [party["name"] for party in node["parties"] or []]



PUBLINOVA_EXTRACTION_OBJECTIVE = {
    # Essential NPPO properties
    "url": PublinovaMetadataExtraction.get_url,
    "files": PublinovaMetadataExtraction.get_files,
    "copyright": PublinovaMetadataExtraction.get_copyright,
    "title": "$.title",
    "language": PublinovaMetadataExtraction.get_language,
    "keywords": PublinovaMetadataExtraction.get_keywords,
    "description": "$.description",
    "mime_type": PublinovaMetadataExtraction.get_mime_type,
    "authors": PublinovaMetadataExtraction.get_authors,
    "provider": PublinovaMetadataExtraction.get_provider,
    "organizations": PublinovaMetadataExtraction.get_organizations,
    "publishers": PublinovaMetadataExtraction.get_publishers,
    "publisher_date": "$.published_at",
    "publisher_year": PublinovaMetadataExtraction.get_publisher_year,

    # # Non-essential NPPO properties
    "technical_type": PublinovaMetadataExtraction.get_technical_type,
    "from_youtube": PublinovaMetadataExtraction.get_from_youtube,
    "is_restricted": PublinovaMetadataExtraction.get_is_restricted,
    "analysis_allowed": PublinovaMetadataExtraction.get_analysis_allowed,
    "research_object_type": "$.research_object_type",
    "research_themes": PublinovaMetadataExtraction.get_research_themes,
    "parties": PublinovaMetadataExtraction.get_parties,
    "doi": "$.doi",

    # Non-essential Edusources properties (for compatibility reasons)
    "material_types": lambda node: None,
    "aggregation_level": lambda node: None,
    "lom_educational_levels": lambda node: [],
    "studies": lambda node: [],
    "ideas": lambda node: [],
    "is_part_of": lambda node: [],
    "has_parts": lambda node: [],
    "copyright_description": lambda node: None,
    "learning_material_disciplines": lambda node: [],
    "consortium": lambda node: None,
    "lom_educational_level": lambda node: None,
    "lowest_educational_level": lambda node: 2,
}
