from datetime import datetime
from dateutil.parser import parse as parse_date

from projects.models import ProjectDocument


class PublinovaProjectExtractor:

    @classmethod
    def get_provider(cls, node):
        return {
            "name": "Publinova",
            "slug": None,
            "ror": None,
            "external_id": None
        }

    @classmethod
    def get_status(cls, node):
        today = datetime.today()
        ended_at = parse_date(node["end_at"]) if node.get("end_at") else None
        started_at = parse_date(node["started_date"]) if node.get("started_date") else None
        if started_at and started_at > today:
            return "to be started"
        elif ended_at and ended_at > today or not ended_at and started_at:
            return "ongoing"
        elif ended_at and ended_at <= today:
            return "finished"
        else:
            return "unknown"

    @classmethod
    def get_keywords(cls, node):
        keywords = node.get("keywords", [])
        return [keyword["label"] for keyword in keywords]

    @classmethod
    def get_parties(cls, node):
        organizations = node.get("parties", [])
        return [organization["name"] for organization in organizations]

    @classmethod
    def get_owners(cls, node):
        owners = node.get("owners", [])
        for owner in owners:
            external_id = owner.pop("external_id") if "external_id" in owner else owner.pop("id")
            owner["external_id"] = external_id
        return owners

    @classmethod
    def get_contacts(cls, node):
        contacts = node.get("contacts", [])
        for contact in contacts:
            external_id = contact.pop("external_id") if "external_id" in contact else contact.pop("id")
            contact["external_id"] = external_id
        return contacts

    @classmethod
    def get_themes(cls, node):
        themes = node.get("themes", [])
        return [theme["label"] for theme in themes]


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$",
    "state": lambda node: ProjectDocument.States.ACTIVE,
    "set": lambda node: "publinova:project",
    "external_id": "$.id",
    "provider": PublinovaProjectExtractor.get_provider,
    # Generic metadata
    "title": "$.title",
    "project_status": PublinovaProjectExtractor.get_status,
    "started_at": "$.started_date",
    "ended_at": "$.end_date",
    "goal": "$.goal",
    "description": "$.description",
    "approach": "$.approach",
    "results": "$.results",
    "keywords": PublinovaProjectExtractor.get_keywords,
    # Research project metadata
    "research_project.contacts": PublinovaProjectExtractor.get_contacts,
    "research_project.owners": PublinovaProjectExtractor.get_owners,
    "research_project.parties": PublinovaProjectExtractor.get_parties,
    "research_project.themes": PublinovaProjectExtractor.get_themes,
}


SEEDING_PHASES = [
    {
        "phase": "projects",
        "strategy": "initial",
        "batch_size": None,
        "retrieve_data": {
            "resource": "projects.huprojectresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
