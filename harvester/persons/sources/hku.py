from persons.models import PersonDocument


def value_or_none(node, key):
    """
    Sometimes an empty value is an empty object.
    This function replaces any falsy values with None.
    """
    return node.get(key, None) or None


class HkuPersonExtractProcessor:

    @classmethod
    def get_provider(cls, node):
        return {
            "name": "Hogeschool voor de Kunsten Utrecht",
            "slug": None,
            "ror": None,
            "external_id": None
        }

    @classmethod
    def get_external_id(cls, node):
        return str(node["personid"])

    @classmethod
    def get_orcid(cls, node):
        return node["ORCID"] or None

    @classmethod
    def get_name(cls, node):
        names = [node["first_name"], node["prefix"], node["last_name"]]
        return " ".join([name for name in names if name])

    @classmethod
    def get_skills(cls, node):
        skills = node.get("skills", {}).get("value", [])
        return skills if isinstance(skills, list) else [skills]

    @classmethod
    def get_themes(cls, node):
        themes = node.get("theme", {}).get("value", [])
        return themes if isinstance(themes, list) else [themes]


OBJECTIVE = {
    # Essential keys for functioning of the system
    "@": "$.root.item",
    "state": lambda node: PersonDocument.States.ACTIVE,
    "set": lambda node: "hku:person",
    "external_id": HkuPersonExtractProcessor.get_external_id,
    "provider": HkuPersonExtractProcessor.get_provider,
    # Generic metadata
    "skills": HkuPersonExtractProcessor.get_skills,
    # Author metadata
    "author.name": HkuPersonExtractProcessor.get_name,
    "author.first_name": "$.first_name",
    "author.last_name": "$.last_name",
    "author.prefix": lambda node: value_or_none(node, "prefix"),
    # Sensitive metadata
    "sensitive.email": lambda node: value_or_none(node, "email"),
    "sensitive.phone": lambda node: None,
    "sensitive.description": lambda node: value_or_none(node, "description"),
    "sensitive.photo_url": "$.photo_url.transcoded",
    # Research based metadata
    "researcher.title": "$.title.value",
    "researcher.themes": HkuPersonExtractProcessor.get_themes,
    "researcher.orcid": HkuPersonExtractProcessor.get_orcid,
}


SEEDING_PHASES = [
    {
        "phase": "persons",
        "strategy": "initial",
        "batch_size": None,
        "retrieve_data": {
            "resource": "persons.hkupersonresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
