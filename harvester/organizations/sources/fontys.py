import os

from sources.utils.pure import PureExtractor


class FontysOrganizationExtraction(PureExtractor):

    source_slug = "fontys"
    source_name = "Fontys Hogescholen"

    @classmethod
    def parse_multilingual_value(cls, value: dict) -> str | None:
        return value.get(
            "nl_NL",
            value.get(
                "en_GB",
                next(iter(value.values()), None)
            )
        )

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
        return cls.parse_multilingual_value(node.get("name", {}))

    @classmethod
    def get_description(cls, node):
        for profile_information in node.get("profileInformation", []):
            profile_information_type = cls.parse_type_value(profile_information.get("type", {}))
            if profile_information_type == "organisation_profile":
                break
        else:
            return None
        return cls.parse_multilingual_value(profile_information.get("value", {}))

    @classmethod
    def get_type(cls, node):
        return cls.parse_type_value(node.get("type", {}))

    @classmethod
    def get_ror(cls, node):
        for identifier in node.get("identifiers", []):
            identifier_type = cls.parse_type_value(identifier.get("type", {}))
            if identifier_type == "ror_id":
                return identifier["id"]

    @classmethod
    def get_parents(cls, node):
        srn_prefix = f"{cls.source_slug}:organization"
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
    "set": lambda node: "fontys:organization",
    "provider": FontysOrganizationExtraction.get_provider,
    # Generic metadata
    "name": FontysOrganizationExtraction.get_name,
    "description": FontysOrganizationExtraction.get_description,
    "ror": FontysOrganizationExtraction.get_ror,
    "type": FontysOrganizationExtraction.get_type,
    "parents": FontysOrganizationExtraction.get_parents,
}


SEEDING_PHASES = [
    {
        "phase": "organizations",
        "strategy": "initial",
        "batch_size": 10,
        "retrieve_data": {
            "resource": "organizations.fontysorganizationresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
