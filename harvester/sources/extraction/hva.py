import re
from mimetypes import guess_type
from hashlib import sha1

from django.conf import settings

from datagrowth.processors import ExtractProcessor


class HvaMetadataExtraction(ExtractProcessor):

    youtube_regex = re.compile(r".*(youtube\.com|youtu\.be).*", re.IGNORECASE)

    @classmethod
    def get_record_state(cls, node):
        return "active"

    #############################
    # GENERIC
    #############################

    @staticmethod
    def _parse_file_url(url):
        file_path_segment = "/ws/api/"
        if file_path_segment not in url:
            return url  # not dealing with a url we recognize as a file url
        start = url.index(file_path_segment)
        file_path = url[start + len(file_path_segment):]
        return f"{settings.SOURCES_MIDDLEWARE_API}files/hva/{file_path}"

    @staticmethod
    def _parse_electronic_version(electronic_version):
        if "file" in electronic_version:
            url = HvaMetadataExtraction._parse_file_url(electronic_version["file"]["url"])
            file_name = electronic_version["file"]["fileName"]
            mime_type = electronic_version["file"]["mimeType"]
        elif "link" in electronic_version:
            url = electronic_version["link"]
            file_name = None
            mime_type = "text/html"
        else:
            return
        access_type = electronic_version.get("accessType", {})
        access_rights = "ClosedAccess"
        if access_type.get("uri", "").endswith("/open"):
            access_rights = "OpenAccess"
        elif access_type.get("uri", "").endswith("/restricted"):
            access_rights = "RestrictedAccess"
        return {
            "title": file_name,
            "url": url,
            "mime_type": mime_type,
            "hash": sha1(url.encode("utf-8")).hexdigest(),
            "copyright": None,
            "access_rights": access_rights
        }

    @classmethod
    def get_files(cls, node):
        electronic_versions = node.get("electronicVersions", []) + node.get("additionalFiles", [])
        if not electronic_versions:
            return []
        return [
            cls._parse_electronic_version(electronic_version)
            for electronic_version in electronic_versions if cls._parse_electronic_version(electronic_version)
        ]

    @classmethod
    def get_language(cls, node):
        language = node["language"]["term"]["en_GB"]
        if language == "Dutch":
            return "nl"
        elif language == "English":
            return "en"
        return "unk"

    @classmethod
    def get_url(cls, node):
        files = cls.get_files(node)
        if not files:
            return node["portalUrl"]
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
    def get_from_youtube(cls, node):
        url = cls.get_url(node)
        if not url:
            return False
        return cls.youtube_regex.match(url) is not None

    @classmethod
    def get_authors(cls, node):
        authors = []
        for person in node["contributors"]:
            name = person.get('name', {})
            match name:
                case {"firstName": first_name}:
                    full_name = f"{first_name} {name['lastName']}"
                case {"lastName": last_name}:
                    full_name = last_name
                case _:
                    # Contributors with the type: ExternalContributorAssociation
                    # do not yield any name or other identity information.
                    # We skip the (useless) data silently
                    continue
            person_data = person.get("person", person.get("externalPerson", {}))
            authors.append({
                "name": full_name,
                "email": None,
                "external_id": person_data.get("uuid",
                                               f"{HvaMetadataExtraction.get_provider(node)['slug']}:person:"
                                               f"{sha1(full_name.encode('utf-8')).hexdigest()}"),
                "dai": None,
                "orcid": None,
                "isni": None
            })
        return authors

    @classmethod
    def get_provider(cls, node):
        return {
            "ror": None,
            "external_id": None,
            "slug": "hva",
            "name": "Hogeschool van Amsterdam"
        }

    @classmethod
    def get_organizations(cls, node):
        root = cls.get_provider(node)
        root["type"] = "institute"
        return {
            "root": root,
            "departments": [],
            "associates": []
        }

    @classmethod
    def get_publishers(cls, node):
        return ["Hogeschool van Amsterdam"]

    @classmethod
    def get_is_restricted(cls, node):
        return not cls.get_analysis_allowed(node)

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
    def get_doi(cls, node):
        if "electronicVersions" not in node:
            return None
        doi_version = next(
            (electronic_version for electronic_version in node["electronicVersions"] if "doi" in electronic_version),
            None
        )
        if not doi_version:
            return None
        doi = doi_version["doi"]
        try:
            return "10." + doi.split("10.", 1)[1].replace(" ", "+")
        except IndexError:
            return None

    @classmethod
    def get_publisher_date(cls, node):
        current_publication = next(
            (publication for publication in node["publicationStatuses"] if publication["current"]),
            None
        )
        if not current_publication:
            return
        publication_date = current_publication["publicationDate"]
        year = publication_date["year"]
        month = publication_date.get("month", 1)
        day = publication_date.get("day", 1)
        return f"{year}-{month:02}-{day:02}"

    @classmethod
    def get_publisher_year(cls, node):
        current_publication = next(
            (publication for publication in node["publicationStatuses"] if publication["current"]),
            None
        )
        if not current_publication:
            return
        return current_publication["publicationDate"]["year"]


HVA_EXTRACTION_OBJECTIVE = {
    # Essential NPPO properties
    "url": HvaMetadataExtraction.get_url,
    "files": HvaMetadataExtraction.get_files,
    "copyright": lambda node: None,
    "title": "$.title.value",
    "language": HvaMetadataExtraction.get_language,
    "keywords": "$.keywordGroups.0.keywords.0.freeKeywords",
    "description": "$.abstract.en_GB",
    "mime_type": HvaMetadataExtraction.get_mime_type,
    "authors": HvaMetadataExtraction.get_authors,
    "provider": HvaMetadataExtraction.get_provider,
    "organizations": HvaMetadataExtraction.get_organizations,
    "publishers": HvaMetadataExtraction.get_publishers,
    "publisher_date": HvaMetadataExtraction.get_publisher_date,
    "publisher_year": HvaMetadataExtraction.get_publisher_year,

    # Non-essential NPPO properties
    "technical_type": HvaMetadataExtraction.get_technical_type,
    "from_youtube": HvaMetadataExtraction.get_from_youtube,
    "is_restricted": HvaMetadataExtraction.get_is_restricted,
    "analysis_allowed": HvaMetadataExtraction.get_analysis_allowed,
    "research_object_type": "$.type.term.en_GB",
    "research_themes": lambda node: [],
    "parties": lambda node: [],
    "doi": HvaMetadataExtraction.get_doi,

    # Non-essential Edusources properties (for compatibility reasons)
    "material_types": lambda node: None,
    "aggregation_level": lambda node: None,
    "lom_educational_levels": lambda node: [],
    "studies": lambda node: [],
    "study_vocabulary": lambda node: [],
    "ideas": lambda node: [],
    "is_part_of": lambda node: [],
    "has_parts": lambda node: [],
    "copyright_description": lambda node: None,
    "learning_material_disciplines": lambda node: [],
    "consortium": lambda node: None,
    "lowest_educational_level": lambda node: 2,
}
