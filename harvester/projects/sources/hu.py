from datetime import datetime
from dateutil.parser import parse as parse_date

from projects.models import ProjectDocument


class HUProjectExtractor:

    @classmethod
    def get_provider(cls, node):
        return {
            "name": "Hogeschool Utrecht",
            "slug": None,
            "ror": None,
            "external_id": None
        }

    @classmethod
    def get_status(cls, node):
        today = datetime.today()
        ended_at = parse_date(node["ended_at"]) if node.get("ended_at") else None
        started_at = parse_date(node["started_at"]) if node.get("started_at") else None
        if started_at and started_at > today:
            return "to be started"
        elif ended_at and ended_at > today or not ended_at and started_at:
            return "ongoing"
        elif ended_at and ended_at <= today:
            return "finished"
        else:
            return "unknown"

    @classmethod
    def get_parties(cls, node):
        organizations = node.get("parties", [])
        return [organization["name"] for organization in organizations]


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$",
    "state": lambda node: ProjectDocument.States.ACTIVE,
    "set": lambda node: "hu:project",
    "external_id": "$.external_id",
    "provider": HUProjectExtractor.get_provider,
    # Generic metadata
    "title": "$.title",
    "project_status": HUProjectExtractor.get_status,
    "started_at": "$.started_at",
    "ended_at": "$.ended_at",
    "coordinates": "$.coordinates",
    "goal": "$.goal",
    "description": "$.description",
    "approach": "$.approach",
    "results": "$.results",
    "persons": "$.persons",
    "keywords": "$.keywords",
    "products": "$.products",
    "photo_url": "$.photo_url",
    # Research project metadata
    "research_project.contacts": "$.contacts",
    "research_project.owners": "$.contacts",  # owners itself is always empty
    "research_project.parties": HUProjectExtractor.get_parties,
    "research_project.themes": "$.research_themes",
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
