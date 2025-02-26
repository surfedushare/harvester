from datetime import datetime

from datagrowth.utils import reach

from projects.models import ProjectDocument


class HkuProjectExtractor:

    #############################
    # UTILS
    #############################

    @classmethod
    def parse_date(cls, date_input):
        if not date_input:
            return
        date = datetime.strptime(date_input, "%d-%M-%Y")
        return date.isoformat()

    @classmethod
    def build_product_srn(cls, identifier):
        if not identifier:
            return identifier
        return f"hku:product:{identifier}"

    @classmethod
    def build_project_srn(cls, identifier):
        if not identifier:
            return identifier
        return f"hku:project:{identifier}"

    @classmethod
    def build_person_srn(cls, identifier):
        if not identifier:
            return identifier
        return f"hku:person:{identifier}"

    #############################
    # EXTRACTION
    #############################

    @classmethod
    def get_external_id(cls, node):
        return str(node["projectid"]) if isinstance(node["projectid"], int) else None

    @classmethod
    def get_srn(cls, node):
        external_id = cls.get_external_id(node)
        return cls.build_project_srn(external_id)

    @classmethod
    def get_provider(cls, node):
        return {
            "name": "Hogeschool voor de Kunsten Utrecht",
            "slug": None,
            "ror": None,
            "external_id": None
        }

    @classmethod
    def get_coordinates(cls, node):
        coordinates = node["coordinates"].replace("lat: ", "").replace("lon: ", "").split(",")
        return coordinates

    @classmethod
    def get_parties(cls, node):
        parties = node["organisations"].get("party", [])
        if not parties or isinstance(parties, dict):  # might be an empty object for some reason
            return []
        return [party["name"] for party in parties if party["name"]]

    @classmethod
    def get_products(cls, node):
        if not node["resultids"]:  # might be an empty object for some reason
            return []
        product_ids = node["resultids"]["ID"] if isinstance(node["resultids"]["ID"], list) else \
            [node["resultids"]["ID"]]
        return [
            cls.build_product_srn(product_id)
            for product_id in product_ids
        ]

    @classmethod
    def get_status(cls, node):
        status_value = "$.status.value"
        match reach(status_value, node):
            case "afgerond":
                return "finished"
            case "in uitvoering":
                return "ongoing"
            case "in voorbereiding":
                return "to be started"
            case _:
                return "unknown"

    @classmethod
    def get_started_at(cls, node):
        return cls.parse_date(node["started_at"])

    @classmethod
    def get_ended_at(cls, node):
        return cls.parse_date(node["ended_at"])

    @staticmethod
    def parse_person_property(node, property_name):
        person = node.get(property_name, None)
        if not person:  # might be an empty object for some reason
            return []
        if isinstance(person, str):
            return [{
                "external_id": None,
                "email": None,
                "name": person
            }]
        return [
            {
                "external_id": None,
                "email": None,
                "name": name
            }
            for name in person["ul"]["li"]
        ]

    @classmethod
    def get_owners(cls, node):
        persons = HkuProjectExtractor.get_persons(node)
        return [persons[0]] if len(persons) else []

    @classmethod
    def get_contacts(cls, node):
        persons = HkuProjectExtractor.get_persons(node)
        return [persons[0]] if len(persons) else []

    @classmethod
    def get_persons(cls, node):
        persons = node.get("persons", {}).get("person", None)
        if persons is None:
            return []
        if isinstance(persons, dict):
            persons = [persons]
        return [
            {
                "external_id": HkuProjectExtractor.build_person_srn(person["person_id"]),
                "email": person.get("email", None),
                "name": f"{person['first_name']} {person['last_name']}"
            }
            for person in persons
        ]

    @classmethod
    def get_keywords(cls, node):
        keywords = node.get("tags").get("value", [])
        return keywords if isinstance(keywords, list) else [keywords]

    @classmethod
    def get_photo_url(cls, node):
        photo_url = node.get("header_image", None)
        photo_url = photo_url or None  # might be an empty object for some reason
        return photo_url


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$.root.project",
    "state": lambda node: ProjectDocument.States.ACTIVE,
    "set": lambda node: "hku:project",
    "external_id": HkuProjectExtractor.get_external_id,
    "provider": HkuProjectExtractor.get_provider,
    # Generic metadata
    "title": "$.title",
    "project_status": HkuProjectExtractor.get_status,
    "started_at": HkuProjectExtractor.get_started_at,
    "ended_at": HkuProjectExtractor.get_ended_at,
    "coordinates": HkuProjectExtractor.get_coordinates,
    "goal": "$.goal",
    "description": "$.description",
    "persons": HkuProjectExtractor.get_persons,
    "keywords": HkuProjectExtractor.get_keywords,
    "products": HkuProjectExtractor.get_products,
    "photo_url": HkuProjectExtractor.get_photo_url,
    # Research project metadata
    "research_project.contacts": HkuProjectExtractor.get_contacts,
    "research_project.owners": HkuProjectExtractor.get_owners,
    "research_project.parties": HkuProjectExtractor.get_parties,
}


SEEDING_PHASES = [
    {
        "phase": "projects",
        "strategy": "initial",
        "batch_size": None,
        "retrieve_data": {
            "resource": "projects.hkuprojectresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
