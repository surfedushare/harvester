import os

from sources.utils.pure import PureExtractor


class HanzeOrganizationExtraction(PureExtractor):

    pure_api_prefix = "/nppo/"
    source_slug = "hanze"
    source_name = "Hanze"

    @classmethod
    def parse_multilingual_value(cls, value: dict) -> str | None:
        return next(iter(value.values()), None)

    @classmethod
    def parse_type_value(cls, value: dict) -> str | None:
        uri = value.get("uri")
        if not uri:
            return None
        prefix, type_value = os.path.split(uri)
        return type_value

    #############################
    # Organization
    #############################

    @classmethod
    def get_name(cls, node):
        return cls.parse_multilingual_value(node["name"])

    @classmethod
    def get_description(cls, node):
        for profile_information in node.get("profileInformations", []):
            profile_information_type = cls.parse_type_value(profile_information["type"])
            if profile_information_type == "organisation_profile":
                break
        else:
            return None
        return cls.parse_multilingual_value(profile_information.get("value", {}))

    @classmethod
    def get_type(cls, node):
        return cls.parse_type_value(node["type"])

    @classmethod
    def get_ror(cls, node):
        for identifier in node.get("identifiers", []):
            identifier_type = cls.parse_type_value(identifier.get("type", {}))
            if identifier_type == "ror_id":
                return identifier["id"]

    @classmethod
    def get_parents(cls, node):
        srn_prefix = f"{cls.source_slug}:hanze"
        return [
            {
                "srn": f"{srn_prefix}:{parent["uuid"]}",
                "name": None
            }
            for parent in node.get("parents", [])
        ]


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$.items",
    "external_id": "$.uuid",
    "state": lambda node: "active",
    "set": lambda node: "hanze:hanze",
    "provider": HanzeOrganizationExtraction.get_provider,
    # Generic metadata
    "name": HanzeOrganizationExtraction.get_name,
    "description": HanzeOrganizationExtraction.get_description,
    "ror": HanzeOrganizationExtraction.get_ror,
    "type": HanzeOrganizationExtraction.get_type,
    "parents": HanzeOrganizationExtraction.get_parents,
}


SEEDING_PHASES = [
    {
        "phase": "organizations",
        "strategy": "initial",
        "batch_size": 10,
        "retrieve_data": {
            "resource": "organizations.hanzeorganizationresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
