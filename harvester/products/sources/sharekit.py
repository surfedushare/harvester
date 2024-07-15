from datetime import datetime
from dateutil.parser import parse as date_parser
from itertools import chain

from sources.utils.sharekit import SharekitExtractor


class SharekitMetadataExtraction:

    @classmethod
    def get_record_state(cls, node):
        return SharekitExtractor.extract_state(node)

    @classmethod
    def get_channel(cls, data):
        return SharekitExtractor.extract_channel(data)

    #############################
    # GENERIC
    #############################

    @classmethod
    def get_files(cls, node):
        files = node["attributes"].get("files", []) or []
        links = node["attributes"].get("links", []) or []
        urls = []
        urls += [SharekitExtractor.parse_url(file_["url"]) for file_ in files if file_.get("url", None)]
        urls += [SharekitExtractor.parse_url(link["url"]) for link in links if link.get("url", None)]
        return urls

    @classmethod
    def get_language(cls, node):
        language = node["attributes"].get("language")
        if not language:
            return "unk"
        return language

    @classmethod
    def get_material_types(cls, node):
        material_types = node["attributes"].get("typesLearningMaterial", [])
        if not material_types:
            return ["unknown"]
        elif isinstance(material_types, list):
            return [material_type for material_type in material_types if material_type]
        else:
            return [material_types]

    @classmethod
    def get_copyright(cls, node):
        return node["attributes"].get("termsOfUse", None)

    @classmethod
    def get_authors(cls, node):
        authors = node["attributes"].get("authors", []) or []
        return [
            {
                "name": author["person"]["name"],
                "email": author["person"]["email"],
                "external_id": author["person"]["id"],
                "dai": author["person"]["dai"],
                "orcid": author["person"]["orcid"],
                "isni": author["person"]["isni"],
            }
            for author in authors
        ]

    @classmethod
    def get_provider(cls, node):
        if not node["attributes"]:
            return
        owner = node["attributes"]["owner"]
        return {
            "ror": None,
            "external_id": owner["id"],
            "slug": None,
            "name": owner["name"]
        }

    @classmethod
    def get_organizations(cls, node):
        root = cls.get_provider(node)
        if not root:
            return
        root["type"] = "unknown"
        return {
            "root": root,
            "departments": [],
            "associates": []
        }

    @classmethod
    def get_consortium(cls, node):
        consortium = node["attributes"].get("consortium", None)
        if consortium is None:
            consortium_keywords = [
                keyword for keyword in node["attributes"].get("keywords", [])
                if "vaktherapie" in keyword.lower()
            ]
            if consortium_keywords:
                consortium = "Projectgroep Vaktherapie"
        return consortium

    @classmethod
    def get_publishers(cls, node):
        publishers = node["attributes"].get("publishers", []) or []
        if isinstance(publishers, str):
            publishers = [publishers]
        keywords = node["attributes"].get("keywords", []) or []
        # Check HBOVPK tags
        hbovpk_keywords = [keyword for keyword in keywords if keyword and "hbovpk" in keyword.lower()]
        if hbovpk_keywords:
            publishers.append("HBO Verpleegkunde")
        return publishers

    @classmethod
    def get_publisher_year(cls, node):
        publisher_date = node["attributes"].get("publishedAt", None)
        if not publisher_date:
            return
        publisher_datetime = date_parser(publisher_date)
        return publisher_datetime.year

    @classmethod
    def get_publisher_date(cls, node):
        publisher_date = node["attributes"].get("publishedAt", None)
        if not publisher_date:
            return
        publisher_datetime = date_parser(publisher_date, default=datetime(year=1970, month=1, day=1))
        return publisher_datetime.strftime("%Y-%m-%d")

    @classmethod
    def get_lom_educational_levels(cls, node):
        educational_levels = node["attributes"].get("educationalLevels", [])
        if not educational_levels:
            return []
        return list(set([
            educational_level["value"] for educational_level in educational_levels
            if educational_level["value"]
        ]))

    @classmethod
    def get_study_vocabulary(cls, node):
        vocabularies = node["attributes"].get("vocabularies", {})
        terms = chain(*vocabularies.values())
        return [term["source"] for term in terms]

    @classmethod
    def get_research_themes(cls, node):
        theme_value = node["attributes"].get("themesResearchObject", [])
        if not theme_value:
            return []
        return theme_value if isinstance(theme_value, list) else [theme_value]

    @classmethod
    def get_learning_material_disciplines(cls, node):
        discipline_value = node["attributes"].get("themesLearningMaterial", [])
        if not discipline_value:
            return []
        return discipline_value if isinstance(discipline_value, list) else [discipline_value]


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$.data",
    "state": SharekitMetadataExtraction.get_record_state,
    "external_id": "$.id",
    "#set": SharekitMetadataExtraction.get_channel,
    # Generic metadata
    "modified_at": "$.attributes.modifiedAt",
    "doi": "$.attributes.doi",
    "files": SharekitMetadataExtraction.get_files,
    "technical_type": "$.attributes.technicalFormat",
    "title": "$.attributes.title",
    "subtitle": "$.attributes.subtitle",
    "language": SharekitMetadataExtraction.get_language,
    "keywords": "$.attributes.keywords",
    "description": "$.attributes.abstract",
    "copyright": SharekitMetadataExtraction.get_copyright,
    "authors": SharekitMetadataExtraction.get_authors,
    "provider": SharekitMetadataExtraction.get_provider,
    "organizations": SharekitMetadataExtraction.get_organizations,
    "publishers": SharekitMetadataExtraction.get_publishers,
    "publisher_date": SharekitMetadataExtraction.get_publisher_date,
    "publisher_year": SharekitMetadataExtraction.get_publisher_year,
    "is_part_of": "$.attributes.partOf",
    "has_parts": "$.attributes.hasParts",
    # Learning material metadata
    "learning_material.aggregation_level": "$.attributes.aggregationlevel",
    "learning_material.material_types": SharekitMetadataExtraction.get_material_types,
    "learning_material.lom_educational_levels": SharekitMetadataExtraction.get_lom_educational_levels,
    "learning_material.study_vocabulary": SharekitMetadataExtraction.get_study_vocabulary,
    "learning_material.disciplines": SharekitMetadataExtraction.get_learning_material_disciplines,
    "learning_material.consortium": SharekitMetadataExtraction.get_consortium,
    # Research product metadata
    "research_product.research_object_type": "$.attributes.typeResearchObject",
    "research_product.research_themes": SharekitMetadataExtraction.get_research_themes,
}


SEEDING_PHASES = [
    {
        "phase": "publications",
        "strategy": "initial",
        "batch_size": 25,
        "retrieve_data": {
            "resource": "sources.sharekitmetadataharvest",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]


WEBHOOK_DATA_TRANSFORMER = SharekitExtractor.webhook_data_transformer


SEQUENCE_PROPERTIES = {  # with tests these properties are used to generate mock data
    "external_id": "{ix}",
    "set": "sharekit:test",
    "title": "Title {ix}",
    "language": "{ix}",
}
