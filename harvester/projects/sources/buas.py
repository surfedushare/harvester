from hashlib import sha1

from sources.utils.pure import PureExtractor, build_seeding_phases
from projects.models import BuasPureProjectResource


class BuasProjectExtractProcessor(PureExtractor):

    source_name = "Breda University of Applied Sciences"
    source_slug = "buas"

    @classmethod
    def get_status(cls, node):
        match node["status"]["key"]:
            case "FINISHED":
                return "finished"
            case "RUNNING":
                return "ongoing"
            case "NOT_STARTED":
                return "to be started"
            case _:
                return "unknown"

    @classmethod
    def get_parties(cls, node):
        return [
            party["externalOrganisation"]["name"]["text"][0]["value"]
            for party in node.get("collaborators", [])
        ]

    @classmethod
    def get_products(cls, node):
        return [product["uuid"] for product in node.get("relatedResearchOutputs", [])]

    @classmethod
    def get_persons(cls, node):
        persons = []
        for participant in node.get("participants", []):
            name = participant.get('name', {})
            match name:
                case {"firstName": first_name}:
                    full_name = f"{first_name} {name['lastName']}"
                case {"lastName": last_name}:
                    full_name = last_name
                case _:
                    # Contributors with the type: ExternalContributorAssociation sometimes
                    # do not yield any name or other identity information.
                    # We skip the (useless) data silently
                    continue
            is_external = "externalPerson" in participant
            person_data = participant.get("person", {}) if not is_external else participant.get("externalPerson", {})
            persons.append({
                "name": full_name,
                "email": None,
                "external_id": person_data.get("uuid",
                                               f"buas:person:"
                                               f"{sha1(full_name.encode('utf-8')).hexdigest()}"),

            })
        return persons

    @classmethod
    def get_owners(cls, node):
        persons = cls.get_persons(node)
        return [persons[0]] if persons else []


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$.items",
    "state": lambda node: "active",
    "set": lambda node: "buas:buas",
    "external_id": "$.uuid",
    "provider": BuasProjectExtractProcessor.get_provider,
    # Project metadata
    "title": "$.title.text.0.value",
    "project_status": BuasProjectExtractProcessor.get_status,
    "started_at": "$.period.startDate",
    "ended_at": "$.period.endDate",
    "coordinates": lambda node: [],
    "description": "$.descriptions.0.value.text.0.value",
    "persons": BuasProjectExtractProcessor.get_persons,
    "keywords": "$.keywordGroups.0.keywordContainers.0.freeKeywords.0.freeKeywords",
    "products": BuasProjectExtractProcessor.get_products,
    # Research project metadata
    "research_project.contacts": BuasProjectExtractProcessor.get_owners,
    "research_project.owners": BuasProjectExtractProcessor.get_owners,
    "research_project.parties": BuasProjectExtractProcessor.get_parties,
}


SEEDING_PHASES = build_seeding_phases(BuasPureProjectResource, OBJECTIVE)
