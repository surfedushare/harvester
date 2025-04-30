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
    "job_title": "$.job_title",
    # Author metadata
    "author.name": "$.name",
    "author.first_name": "$.first_name",
    "author.last_name": "$.last_name",
    "author.prefix": "$.prefix",
    "author.initials": "$.initials",
    "author.isni": "$.isni",
    # Sensitive metadata
    "sensitive.description": "$.description",
    "sensitive.email": "$.email",
    "sensitive.phone": "$.phone",
    "sensitive.photo_url": "$.photo_url",
    # Research based metadata
    "researcher.title": "$.title",  # academic title
    "researcher.themes": "$.themes",
    "researcher.dai": "$.dai",
    "researcher.orcid": "$.orcid",
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
