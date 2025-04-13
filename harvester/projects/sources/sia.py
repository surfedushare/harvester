from django.conf import settings

from datagrowth.utils import reach
from projects.models import ProjectDocument


class SiaProjectExtraction:

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

    @classmethod
    def get_started_at(cls, node):
        started_at = reach("$.startdatum", node)
        if not started_at:
            return None
        return started_at.replace(" 00:00:00", "")

    @classmethod
    def get_ended_at(cls, node):
        ended_at = reach("$.einddatum", node)
        if not ended_at:
            return None
        return ended_at.replace(" 00:00:00", "")


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$",
    "state": SiaProjectExtraction.get_state,
    "set": lambda node: "sia:project",
    "merge_id": "$.id",
    "external_id": lambda node: str(node["id"]),
    "provider": SiaProjectExtraction.get_provider,
    # Generic metadata
    "title": SiaProjectExtraction.get_title,
    "project_status": SiaProjectExtraction.get_status,
    "started_at": SiaProjectExtraction.get_started_at,
    "ended_at": SiaProjectExtraction.get_ended_at,
    "goal": "$.eindrapportage",
    "description": "$.samenvatting",
    # Research project metadata
    "research_project.sia_project_reference": "$.dossiernummer",
    "research_project.owners": SiaProjectExtraction.get_owner_and_contact,
    "research_project.contacts": SiaProjectExtraction.get_owner_and_contact,
    "research_project.parties": SiaProjectExtraction.get_parties,
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
            "backoff_delays": [30, 45, 60, 30, 45, 60],
        },
        "contribute_data": {
            "objective": {
                "@": "$",
                "state": lambda node: "inactive",
                "set": lambda node: "sia:project",
                "merge_id": "$.id",
                "external_id": "$.id",
                "provider": SiaProjectExtraction.get_provider,
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
            "backoff_delays": [30, 45, 60, 30, 45, 60],
        },
        "contribute_data": {
            "merge_on": "merge_id",
            "objective": OBJECTIVE
        }
    }
]
