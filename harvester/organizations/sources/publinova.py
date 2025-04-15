class PublinovaOrganizationExtraction:

    @classmethod
    def get_type(cls, node):
        type_value = node.get("type")
        return type_value.lower() if type_value else None


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$.data",
    "state": lambda node: "active",
    "external_id": "$.id",
    "set": lambda node: "publinova:organization",
    "provider": lambda node: {"name": "Publinova"},
    # Generic metadata
    "name": "$.name",
    "description": "$.description",
    "ror": "$.ror",
    "type": PublinovaOrganizationExtraction.get_type,
}


SEEDING_PHASES = [
    {
        "phase": "organizations",
        "strategy": "initial",
        "batch_size": 25,
        "retrieve_data": {
            "resource": "organizations.publinovaorganizationresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
