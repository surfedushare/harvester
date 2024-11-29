from django.conf import settings

from core.constants import Platforms
from sources.utils.sharekit import SharekitExtractor


class SharekitOrganizationExtraction:

    PLATFORM_TO_CHANNEL = {
        Platforms.EDUSOURCES: "edusources",
        Platforms.PUBLINOVA: "nppo",
        Platforms.MBODATA: "edusourcesmbo",
    }

    @classmethod
    def get_record_state(cls, node):
        state = SharekitExtractor.extract_state(node)
        return state if not node["attributes"].get("inactive") == 1 else "deleted"

    @classmethod
    def get_set(cls, data):
        return f"sharekit:{cls.PLATFORM_TO_CHANNEL[settings.PLATFORM]}"

    #############################
    # Organization
    #############################

    @classmethod
    def get_parents(cls, node):
        if not (parent_name := node["attributes"].get("parentName")):
            return []
        srn_prefix = cls.get_set(node)
        parent_id = node["attributes"].get("parentId")
        return [{
            "srn": f"{srn_prefix}:{parent_id}",
            "name": parent_name,
        }]

    @classmethod
    def get_secretary(cls, node):
        if not (collaborators := node["attributes"].get("consortiumChildren")):
            return
        secretary = next((collaborator for collaborator in collaborators if collaborator["secretary"]), None)
        if not secretary:
            return
        srn_prefix = cls.get_set(node)
        return {
            "srn": f"{srn_prefix}:{secretary["id"]}",
            "name": secretary["name"],
            "ror": secretary["ror"],
            "is_root": None
        }

    @classmethod
    def get_members(cls, node):
        if not (collaborators := node["attributes"].get("consortiumChildren")):
            return []
        srn_prefix = cls.get_set(node)
        return [
            {
                "srn": f"{srn_prefix}:{collaborator["id"]}",
                "name": collaborator["name"],
            }
            for collaborator in collaborators if not collaborator["secretary"]
        ]


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$.data",
    "state": SharekitOrganizationExtraction.get_record_state,
    "external_id": "$.id",
    "#set": SharekitOrganizationExtraction.get_set,
    "provider": lambda node: {"name": "SURFSharekit"},
    # Generic metadata
    "name": "$.attributes.name",
    "description": "$.attributes.description",
    "ror": "$.attributes.ror",
    "type": "$.attributes.level",
    "secretary": SharekitOrganizationExtraction.get_secretary,
    "parents": SharekitOrganizationExtraction.get_parents,
    "members": SharekitOrganizationExtraction.get_members,
}


SEEDING_PHASES = [
    {
        "phase": "organizations",
        "strategy": "initial",
        "batch_size": 25,
        "retrieve_data": {
            "resource": "organizations.sharekitorganizationresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
