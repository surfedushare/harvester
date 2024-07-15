import os
from typing import Type
from hashlib import sha1

from sources.utils.pure import PureExtractor


class PureProductExtraction(PureExtractor):

    support_subtitle = False
    authors_property = "contributors"
    file_url_property = "url"

    @classmethod
    def get_files(cls, node):
        electronic_versions = node.get("electronicVersions", []) + node.get("additionalFiles", [])
        if not electronic_versions:
            return []
        files = []
        for electronic_version in electronic_versions:
            if "file" in electronic_version:
                normalized_url = cls.parse_url(electronic_version["file"][cls.file_url_property])
                url = cls._parse_file_url(normalized_url)
            elif "link" in electronic_version:
                url = electronic_version["link"]
            else:
                continue
            files.append(url)
        return files

    @classmethod
    def get_locale(cls, node):
        locale_uri = node["language"]["uri"]
        _, locale = os.path.split(locale_uri)
        return locale

    @classmethod
    def get_language(cls, node):
        locale = cls.get_locale(node)
        if locale in ["en_GB", "nl_NL"]:
            return locale[:2]
        return "unk"

    @classmethod
    def get_title(cls, node):
        title = node["title"]["value"]
        if "subTitle" in node and cls.support_subtitle:
            subtitle = node["subTitle"]["value"]
            title = f"{title}: {subtitle}"
        return title

    @classmethod
    def get_description(cls, node):
        if "abstract" not in node:
            return
        locale = cls.get_locale(node)
        fallback_description = next(iter(node["abstract"].values()), None)
        return node["abstract"].get(locale, fallback_description)

    @classmethod
    def get_keywords(cls, node):
        results = []
        for keywords in node.get("keywordGroups", []):
            match keywords["logicalName"]:
                case "keywordContainers":
                    for free_keywords in keywords["keywords"]:
                        results += free_keywords.get("freeKeywords", [])
        return list(set(results))

    @classmethod
    def get_authors(cls, node):
        authors = []
        for person in node[cls.authors_property]:
            name = person.get('name', {})
            match name:
                case {"firstName": first_name}:
                    full_name = f"{first_name} {name['lastName']}"
                case {"lastName": last_name}:
                    full_name = last_name
                case _:
                    # Contributors with the type: ExternalContributorAssociation sometimes
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
        # We'll put the first organization author as first author in the list
        # Within Publinova this person will become the owner and contact person
        first_organization_author_index = next(
            (ix for ix, person in enumerate(node[cls.authors_property]) if "externalPerson" not in person),
            None
        )
        if authors and first_organization_author_index is not None:
            first_organization_author = authors.pop(first_organization_author_index)
            authors = [first_organization_author] + authors
        return authors

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

    @classmethod
    def get_research_themes(cls, node):
        return []


def build_objective(extract_processor: Type[PureProductExtraction], source_set: str, api_version: str = "v2") -> dict:
    if api_version == "v2":
        description_extractor = extract_processor.get_description
        object_type_extractor = "$.type.term.en_GB"
        modified_at_extractor = "$.modifiedDate"
    elif api_version == "v1":
        description_extractor = "$.abstract.text.0.value"
        object_type_extractor = "$.type.term.text.0.value"
        modified_at_extractor = "$.info.modifiedDate"
    else:
        raise ValueError(f"Unexpected Pure API version: {api_version}")
    return {
        # Essential objective keys for system functioning
        "@": "$.items",
        "external_id": "$.uuid",
        "state": lambda node: "active",
        "set": lambda node: source_set,
        # Generic metadata
        "modified_at": modified_at_extractor,
        "doi": extract_processor.get_doi,
        "files": extract_processor.get_files,
        "title": extract_processor.get_title,
        "language": extract_processor.get_language,
        "keywords": extract_processor.get_keywords,
        "description": description_extractor,
        "authors": extract_processor.get_authors,
        "provider": extract_processor.get_provider,
        "organizations": extract_processor.get_organizations,
        "publishers": extract_processor.get_publishers,
        "publisher_date": extract_processor.get_publisher_date,
        "publisher_year": extract_processor.get_publisher_year,
        # Research product metadata
        "research_product.research_object_type": object_type_extractor,
        "research_product.research_themes": extract_processor.get_research_themes,
    }
