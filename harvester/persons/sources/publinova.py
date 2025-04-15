from persons.models import PersonDocument


class PublinovaPersonExtractProcessor:

    @classmethod
    def get_provider(cls, node):
        return {
            "name": "Publinova",
            "slug": None,
            "ror": None,
            "external_id": None
        }


OBJECTIVE = {
    # Essential keys for functioning of the system
    "@": "$.data",
    "state": lambda node: PersonDocument.States.ACTIVE,
    "set": lambda node: "publinova:person",
    "external_id": "$.id",
    "provider": PublinovaPersonExtractProcessor.get_provider,
    # Author metadata
    "author.name": "$.name",
    "author.isni": "$.isni",
    # Sensitive metadata
    "sensitive.email": "$.email",
    "sensitive.description": "$.about",
    # Research based metadata
    "researcher.orcid": "$.orcid",
    "researcher.dai": "$.dai",
}


SEEDING_PHASES = [
    {
        "phase": "persons",
        "strategy": "initial",
        "batch_size": None,
        "retrieve_data": {
            "resource": "persons.publinovapersonresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
