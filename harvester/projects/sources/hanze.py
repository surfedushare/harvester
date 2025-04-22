import os
from hashlib import sha1
from datetime import UTC
from dateutil.parser import parse as date_parser

from django.utils.timezone import now

from sources.constants.hanze import FOCUS_AREA_TO_RESEARCH_THEME
from sources.utils.pure import PureExtractor, build_seeding_phases
from projects.models import HanzePureProjectResource


class HanzeProjectExtractProcessor(PureExtractor):

    source_name = "Hanze"
    source_slug = "hanze"

    @classmethod
    def get_status(cls, node):
        period = node.get("period")
        if not period:
            return "unknown"
        today = now()
        ended_at = date_parser(period["endDate"]).replace(tzinfo=UTC) if period.get("endDate") else None
        started_at = date_parser(period["startDate"]).replace(tzinfo=UTC) if period.get("startDate") else None
        if started_at and started_at > today:
            return "to be started"
        elif ended_at and ended_at > today or not ended_at and started_at:
            return "ongoing"
        elif ended_at and ended_at <= today:
            return "finished"
        else:
            return "unknown"

    @classmethod
    def get_title(cls, node):
        return node["title"].get("nl_NL", next(iter(node["title"].values())))

    @classmethod
    def get_description(cls, node):
        # Gather all possible descriptions
        descriptions = {}
        for description in node["descriptions"]:
            if "value" not in description:
                continue
            description_type = os.path.split(description["type"]["uri"])[1]
            description_text = description["value"].get("nl_NL", next(iter(description["value"].values())))
            if description_text:
                descriptions[description_type] = description_text
        # Concatenate different descriptions to be a singular text
        description = ""
        if "laymansdescription" in descriptions:
            description += descriptions["laymansdescription"]

        if "keyfindings" in descriptions:
            if description:
                description += "</br></br>"
            description += descriptions["keyfindings"]
        if "projectdescription" in descriptions:
            if description:
                description += "</br></br>"
            description += descriptions["projectdescription"]
        return description or None

    @classmethod
    def get_keywords(cls, node):
        keyword_groups = [
            keyword_group for keyword_group in node.get("keywordGroups", [])
            if keyword_group.get("logicalName", None) == "keywordContainers"
        ]
        if not keyword_groups:
            return []
        keywords = []
        for keyword_group in keyword_groups:
            keywords += keyword_group["keywords"][0]["freeKeywords"]
        return keywords

    @classmethod
    def get_products(cls, node):
        set_name = f"{cls.source_slug}:{cls.source_slug}"
        return [f"{set_name}:{product["researchOutput"]["uuid"]}" for product in node.get("researchOutputs", [])]

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
            is_external = "externalPerson" in participant or \
                          "external" in participant.get("typeDiscriminator", "").lower()
            person_data = participant.get("person", {}) if not is_external else participant.get("externalPerson", {})
            persons.append({
                "name": full_name,
                "email": None,
                "external_id": person_data.get("uuid",
                                               f"hanze:person:"
                                               f"{sha1(full_name.encode('utf-8')).hexdigest()}"),
                "is_external": is_external,
            })
        return persons

    @classmethod
    def get_owners(cls, node):
        persons = cls.get_persons(node)
        return [persons[0]] if persons else []

    @classmethod
    def get_research_themes(cls, node):
        research_themes = []
        for keywords in node.get("keywordGroups", []):
            if keywords["logicalName"] == "research_focus_areas":
                for classification in keywords["classifications"]:
                    if classification["uri"] in FOCUS_AREA_TO_RESEARCH_THEME.keys():
                        research_themes.append(FOCUS_AREA_TO_RESEARCH_THEME[classification["uri"]])
        return research_themes


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$.items",
    "state": lambda node: "active",
    "set": lambda node: "hanze:project",
    "external_id": "$.uuid",
    "provider": HanzeProjectExtractProcessor.get_provider,
    # # Project metadata
    "title": HanzeProjectExtractProcessor.get_title,
    "project_status": HanzeProjectExtractProcessor.get_status,
    "started_at": "$.period.startDate",
    "ended_at": "$.period.endDate",
    "description": HanzeProjectExtractProcessor.get_description,
    "persons": HanzeProjectExtractProcessor.get_persons,
    "keywords": HanzeProjectExtractProcessor.get_keywords,
    "products": HanzeProjectExtractProcessor.get_products,
    # # Research project metadata
    "research_project.contacts": HanzeProjectExtractProcessor.get_owners,
    "research_project.owners": HanzeProjectExtractProcessor.get_owners,
    "research_project.themes": HanzeProjectExtractProcessor.get_research_themes,
}


SEEDING_PHASES = build_seeding_phases(HanzePureProjectResource, OBJECTIVE)
