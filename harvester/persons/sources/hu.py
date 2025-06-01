from datagrowth.utils import reach

from persons.models import PersonDocument


class HUPersonExtractor:

    @classmethod
    def get_provider(cls, node):
        return {
            "name": "Hogeschool Utrecht",
            "slug": "hu",
            "ror": None,
            "external_id": None
        }


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$",
    "state": lambda node: PersonDocument.States.ACTIVE,
    "set": lambda node: "hu:person",
    "external_id": "$.external_id",
    "provider": HUPersonExtractor.get_provider,
    # Generic metadata
    "skills": "$.skills",
    "organizations": "$.parties",
    "is_employed": "$.is_employed",
    "job_title": lambda node: reach("$.job_title", node) or None,
    # Author metadata
    "author.name": "$.name",
    "author.first_name": "$.first_name",
    "author.last_name": "$.last_name",
    "author.prefix": "$.prefix",
    "author.initials": "$.initials",
    "author.isni": lambda node: reach("$.isni", node) or None,
    # Sensitive metadata
    "sensitive.description": lambda node: reach("$.description", node) or None,
    "sensitive.email": lambda node: reach("$.email", node) or None,
    "sensitive.phone": lambda node: reach("$.phone", node) or None,
    "sensitive.photo_url": lambda node: reach("$.photo_url", node) or None,
    # Research based metadata
    "researcher.title": lambda node: reach("$.title", node) or None,  # academic title
    "researcher.themes": "$.themes",
    "researcher.dai": lambda node: reach("$.dai", node) or None,
    "researcher.orcid": lambda node: reach("$.orcid", node) or None,
    "researcher.research_themes": "$.research_themes",
}


SEEDING_PHASES = [
    {
        "phase": "persons",
        "strategy": "initial",
        "batch_size": None,
        "retrieve_data": {
            "resource": "persons.hupersonresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
