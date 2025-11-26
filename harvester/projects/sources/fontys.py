from hashlib import sha1

from datagrowth.utils import reach

from sources.utils.pure import PureExtractor, build_seeding_phases
from projects.models import FontysPureProjectResource


class FontysProjectExtractProcessor(PureExtractor):

    source_name = "Fontys Hogescholen"
    source_slug = "fontys"

    @classmethod
    def get_status(cls, node):
        match node.get("status", {}).get("key"):
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
        parties = []
        for collaborator in node.get("collaborators", []):
            external_org = collaborator.get("externalOrganization", {})
            if external_org:
                name = external_org.get("name", {})
                party_name = name.get("nl_NL", name.get("en_GB"))
                if party_name:
                    parties.append(party_name)
        return parties

    @classmethod
    def get_products(cls, node):
        return [product["uuid"] for product in node.get("relatedResearchOutputs", [])]

    @classmethod
    def get_keywords(cls, node):
        keywords = []
        for keyword_group in node.get("keywordGroups", []):
            if keyword_group.get("logicalName") == "keywordContainers":
                for keyword_item in keyword_group.get("keywords", []):
                    keywords.extend(keyword_item.get("freeKeywords", []))
        return keywords

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
                    # Contributors without name information are skipped
                    continue
            is_external = "externalPerson" in participant or "person" not in participant
            person_data = participant.get("person", {}) if not is_external else participant.get("externalPerson", {})
            persons.append({
                "name": full_name,
                "email": None,
                "external_id": person_data.get("uuid",
                                               f"fontys:person:"
                                               f"{sha1(full_name.encode('utf-8')).hexdigest()}"),
                "is_external": is_external,
            })
        return persons

    @classmethod
    def get_owners(cls, node):
        persons = cls.get_persons(node)
        return [persons[0]] if persons else []

    @classmethod
    def get_description(cls, node):
        descriptions = node.get("descriptions", [])
        if descriptions:
            desc = descriptions[0].get("value", {})
            return desc.get("nl_NL", desc.get("en_GB"))
        return None

    @classmethod
    def get_title(cls, node):
        title = node.get("title", {})
        return title.get("nl_NL", title.get("en_GB"))


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$.items",
    "state": lambda node: "active",
    "set": lambda node: "fontys:project",
    "external_id": "$.uuid",
    "provider": FontysProjectExtractProcessor.get_provider,
    # Project metadata
    "title": FontysProjectExtractProcessor.get_title,
    "project_status": FontysProjectExtractProcessor.get_status,
    "started_at": "$.period.startDate",
    "ended_at": "$.period.endDate",
    "coordinates": lambda node: [],
    "description": FontysProjectExtractProcessor.get_description,
    "persons": FontysProjectExtractProcessor.get_persons,
    "keywords": FontysProjectExtractProcessor.get_keywords,
    "products": FontysProjectExtractProcessor.get_products,
    # Research project metadata
    "research_project.contacts": FontysProjectExtractProcessor.get_owners,
    "research_project.owners": FontysProjectExtractProcessor.get_owners,
    "research_project.parties": FontysProjectExtractProcessor.get_parties,
}


SEEDING_PHASES = build_seeding_phases(FontysPureProjectResource, OBJECTIVE)
