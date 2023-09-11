from hashlib import sha1
from dateutil.parser import parse as date_parser
from itertools import chain

from datagrowth.processors import ExtractProcessor


class SharekitMetadataExtraction(ExtractProcessor):

    @classmethod
    def get_record_state(cls, node):
        return node.get("meta", {}).get("status", "active")

    #############################
    # GENERIC
    #############################

    @classmethod
    def get_srn(cls, node: dict) -> str:
        provider = SharekitMetadataExtraction.get_provider(node)["name"]
        return f"sharekit:{provider}:{node['id']}"

    @classmethod
    def get_files(cls, node):
        provider = SharekitMetadataExtraction.get_provider(node)["name"]
        files = node["attributes"].get("files", []) or []
        links = node["attributes"].get("links", []) or []
        output = [
            f"sharekit:{provider}:{sha1(file['url'].encode('utf-8')).hexdigest()}" for file in files
            if file.get("url", None)
        ]
        output += [
            f"sharekit:{provider}:{sha1(link['url'].encode('utf-8')).hexdigest()}" for link in links
            if link.get("url", None)
        ]
        return output

    @classmethod
    def get_material_types(cls, node):
        material_types = node["attributes"].get("typesLearningMaterial", [])
        if not material_types:
            return []
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
        provider_name = None
        publishers = cls.get_publishers(node)
        if isinstance(publishers, str):
            provider_name = publishers
        if len(publishers):
            provider_name = publishers[0]
        return {
            "ror": None,
            "external_id": None,
            "slug": None,
            "name": provider_name
        }

    @classmethod
    def get_organizations(cls, node):
        root = cls.get_provider(node)
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
    def get_lom_educational_levels(cls, node):
        educational_levels = node["attributes"].get("educationalLevels", [])
        if not educational_levels:
            return []
        return list(set([
            educational_level["value"] for educational_level in educational_levels
            if educational_level["value"]
        ]))

    @classmethod
    def get_ideas(cls, node):
        vocabularies = node["attributes"].get("vocabularies", {})
        terms = chain(*vocabularies.values())
        compound_ideas = [term["value"] for term in terms]
        if not compound_ideas:
            return []
        ideas = []
        for compound_idea in compound_ideas:
            ideas += compound_idea.split(" - ")
        return list(set(ideas))

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
    "@": "$.data",
    "state": SharekitMetadataExtraction.get_record_state,
    "srn": SharekitMetadataExtraction.get_srn,

    "doi": "$.attributes.doi",
    "files": SharekitMetadataExtraction.get_files,
    "title": "$.attributes.title",
    "language": "$.attributes.language",
    "keywords": "$.attributes.keywords",
    "description": "$.attributes.abstract",

    "copyright": SharekitMetadataExtraction.get_copyright,
    "copyright_description": lambda node: None,
    "authors": SharekitMetadataExtraction.get_authors,
    "provider": SharekitMetadataExtraction.get_provider,
    "organizations": SharekitMetadataExtraction.get_organizations,
    "publishers": SharekitMetadataExtraction.get_publishers,
    "publisher_date": "$.attributes.publishedAt",
    "publisher_year": SharekitMetadataExtraction.get_publisher_year,
    "is_part_of": "$.attributes.partOf",
    "has_parts": "$.attributes.hasParts",

    "learning_material.aggregation_level": "$.attributes.aggregationlevel",
    "learning_material.material_types": SharekitMetadataExtraction.get_material_types,
    "learning_material.lom_educational_levels": SharekitMetadataExtraction.get_lom_educational_levels,
    "learning_material.studies": lambda node: [],
    "learning_material.ideas": SharekitMetadataExtraction.get_ideas,
    "learning_material.study_vocabulary": SharekitMetadataExtraction.get_study_vocabulary,
    "learning_material.disciplines": SharekitMetadataExtraction.get_learning_material_disciplines,
    "learning_material.consortium": SharekitMetadataExtraction.get_consortium,

    "research_product.research_object_type": "$.attributes.typeResearchObject",
    "research_product.research_themes": SharekitMetadataExtraction.get_research_themes,
    "research_product.parties": lambda node: [],
}


SEEDING_PHASES = [
    {
        "phase": "publications",
        "strategy": "initial",
        "batch_size": 25,
        "retrieve_data": {
            "resource": "sharekit.sharekitmetadataharvest",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
