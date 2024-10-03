from django.conf import settings

from projects.models import ProjectDocument


class SiaProjectExtraction:

    @classmethod
    def get_external_id(cls, node):
        if not node["id"]:
            return
        return f"project:{node['id']}"

    @classmethod
    def get_state(cls, node):
        if not node.get("status"):
            return ProjectDocument.States.DELETED
        return ProjectDocument.States.ACTIVE

    @classmethod
    def get_provider(cls, node):
        return {
            "name": "SIA",
            "slug": None,
            "ror": None,
            "external_id": None
        }

    @classmethod
    def get_title(cls, node):
        return node.get("titel") or ""

    @classmethod
    def get_status(cls, node):
        match node.get("status"):
            case "Afgerond":
                return "finished"
            case _:
                return "unknown"

    @classmethod
    def get_parties(cls, node):
        contact_parties = [node["contactinformatie"]["naam"]] if node.get("contactinformatie") else []
        network_parties = [network_party["naam"] for network_party in node.get("netwerkleden", [])]
        consortium_parties = [network_party["naam"] for network_party in node.get("consortiumpartners", [])]
        return contact_parties + consortium_parties + network_parties

    @classmethod
    def get_owner_and_contact(cls, node):
        return [{
            "external_id": None,
            "email": settings.SOURCES["sia"]["contact_email"],
            "name": None
        }]


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$",
    "state": SiaProjectExtraction.get_state,
    "set": lambda node: "sia:sia",
    "merge_id": "$.id",  #
    "external_id": SiaProjectExtraction.get_external_id,
    "provider": SiaProjectExtraction.get_provider,
    # Generic metadata
    "title": SiaProjectExtraction.get_title,
    "project_status": SiaProjectExtraction.get_status,
    "started_at": "$.startdatum",
    "ended_at": "$.einddatum",
    "coordinates": lambda node: [],
    "goal": "$.eindrapportage",
    "description": "$.samenvatting",
    "persons": lambda node: [],
    "keywords": lambda node: [],
    "products": lambda node: [],
    "photo_url": lambda node: None,
    # Research project metadata
    "research_project.owners": SiaProjectExtraction.get_owner_and_contact,
    "research_project.contacts": SiaProjectExtraction.get_owner_and_contact,
    "research_project.parties": SiaProjectExtraction.get_parties,
    "research_project.themes": lambda node: [],
}


SEEDING_PHASES = [
    {
        "phase": "ids",
        "strategy": "initial",
        "batch_size": 25,
        "retrieve_data": {
            "resource": "projects.siaprojectidsresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": {
                "@": "$",
                "merge_id": "$.id"
            }
        }
    },
    {
        "phase": "details",
        "strategy": "merge",
        "batch_size": None,
        "retrieve_data": {
            "resource": "projects.siaprojectdetailsresource",
            "method": "get",
            "args": [
                "$.merge_id"
            ],
            "kwargs": {},
        },
        "contribute_data": {
            "merge_on": "merge_id",
            "objective": OBJECTIVE
        }
    }
]
