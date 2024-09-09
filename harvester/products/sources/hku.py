from datetime import datetime
from dateutil.parser import parse as date_parser

from sources.utils.hku import HkuExtractor


class HkuProductExtraction(HkuExtractor):

    @classmethod
    def get_record_state(cls, node):
        return "deleted" if node["deleted"] else "active"

    #############################
    # GENERIC
    #############################

    @classmethod
    def get_files(cls, node):
        document = node["document"]
        if not document:
            return []
        file_object = document["file"]
        return [file_object["raw"]]

    @classmethod
    def get_language(cls, node):
        language = node["language"]
        if language == "Nederlands":
            return "nl"
        elif language == "Engels":
            return "en"
        return

    @classmethod
    def get_copyright(cls, node):
        if node["licence"] == "Niet commercieel - geen afgeleide werken (CC BY-NC-ND)":
            return "cc-by-nc-nd-40"
        return "yes"

    @classmethod
    def get_keywords(cls, node):
        tags = node["tags"]
        if not tags:
            return []
        return tags.split(", ")

    @classmethod
    def get_authors(cls, node):
        if not node["persons"]:
            return []
        if isinstance(node["persons"]["person"], dict):
            node["persons"]["person"] = [node["persons"]["person"]]
        return [
            {
                "name": cls.build_full_name(person),
                "email": person["email"] or None,
                "external_id": cls.build_person_id(person.get("person_id", None)),
                "dai": None,
                "orcid": None,
                "isni": None,
                "is_external": False,
            }
            for person in node["persons"]["person"]
        ]

    @classmethod
    def get_publisher_year(cls, node):
        date = date_parser(node["date"])
        return date.year

    @classmethod
    def get_publisher_date(cls, node):
        publisher_date = node.get("date", None)
        if not publisher_date:
            return
        publisher_datetime = date_parser(publisher_date, default=datetime(year=1970, month=1, day=1))
        return publisher_datetime.strftime("%Y-%m-%d")

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
        return ["Hogeschool voor de Kunsten Utrecht"]

    @classmethod
    def get_modified_at(cls, node):
        modified_at = date_parser(node["datelastmodified"])
        return modified_at.strftime("%Y-%m-%d")


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$.root.item",
    "external_id": HkuProductExtraction.get_external_id,
    "state": HkuProductExtraction.get_record_state,
    "set": lambda node: "hku:hku",
    # Generic metadata
    "modified_at": HkuProductExtraction.get_modified_at,
    "files": HkuProductExtraction.get_files,
    "copyright": HkuProductExtraction.get_copyright,
    "title": "$.title",
    "language": HkuProductExtraction.get_language,
    "keywords": HkuProductExtraction.get_keywords,
    "description": "$.description",
    "authors": HkuProductExtraction.get_authors,
    "provider": HkuProductExtraction.get_provider,
    "organizations": HkuProductExtraction.get_organizations,
    "publishers": HkuProductExtraction.get_publishers,
    "publisher_date": HkuProductExtraction.get_publisher_date,
    "publisher_year": HkuProductExtraction.get_publisher_year,
}

SEEDING_PHASES = [
    {
        "phase": "items",
        "strategy": "initial",
        "batch_size": 100,
        "retrieve_data": {
            "resource": "sources.hkumetadataresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
