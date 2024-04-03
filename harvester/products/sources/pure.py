from typing import Type
from hashlib import sha1

from django.conf import settings

from sources.utils.base import BaseExtractor


class PureProductExtraction(BaseExtractor):

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

    @classmethod
    def get_files(cls, node):
        electronic_versions = node.get("electronicVersions", []) + node.get("additionalFiles", [])
        if not electronic_versions:
            return []
        files = []
        for electronic_version in electronic_versions:
            if "file" in electronic_version:
                normalized_url = cls.parse_url(electronic_version["file"]["url"])
                url = cls._parse_file_url(normalized_url)
            elif "link" in electronic_version:
                url = electronic_version["link"]
            else:
                continue
            files.append(url)
        return files

    @classmethod
    def get_language(cls, node):
        language = node["language"]["term"]["en_GB"]
        if language == "Dutch":
            return "nl"
        elif language == "English":
            return "en"
        return "unk"

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
                                               f"{cls.get_provider(node)['slug']}:person:"
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


def build_objective(extract_processor: Type[PureProductExtraction], source_set: str) -> dict:
    return {
        # Essential objective keys for system functioning
        "@": "$.items",
        "external_id": "$.uuid",
        "state": lambda node: "active",
        "set": lambda node: source_set,
        # Generic metadata
        "modified_at": "$.modifiedDate",
        "doi": extract_processor.get_doi,
        "files": extract_processor.get_files,
        "title": "$.title.value",
        "language": extract_processor.get_language,
        "keywords": "$.keywordGroups.0.keywords.0.freeKeywords",
        "description": "$.abstract.en_GB",
        "authors": extract_processor.get_authors,
        "provider": extract_processor.get_provider,
        "organizations": extract_processor.get_organizations,
        "publishers": extract_processor.get_publishers,
        "publisher_date": extract_processor.get_publisher_date,
        "publisher_year": extract_processor.get_publisher_year,
        # Research product metadata
        "research_product.research_object_type": "$.type.term.en_GB",
        "research_product.research_themes": lambda node: [],
    }
