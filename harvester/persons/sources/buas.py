import os
from datetime import datetime
from dateutil.parser import parse as date_parser

from django.utils.html import strip_tags

from persons.models import PersonDocument


class BuasPersonExtractProcessor:

    @classmethod
    def parse_profile_information(cls, node, info_type):
        for profile_information in node.get("profileInformations", []):
            profile_information_uri = profile_information.get("type").get("uri")
            _, profile_information_type = os.path.split(profile_information_uri)
            if profile_information_type == info_type:
                return profile_information.get("value").get("text")[0].get("value")

    @classmethod
    def get_legacy_valid_staff_organization_association(cls, node, required_attribute=None):
        today = datetime.today()
        for association in node.get("staffOrganisationAssociations", []):  # organization spelled with a 's'
            end_date = association.get("period", None).get("endDate", None)
            if not end_date or date_parser(end_date, ignoretz=True) > today:
                if not required_attribute:
                    break
                elif association.get(required_attribute):
                    break
        else:
            return
        return association

    @classmethod
    def get_provider(cls, node):
        return {
            "name": "Breda University of Applied Sciences",
            "slug": "buas",
            "ror": None,
            "external_id": None
        }

    @classmethod
    def get_name(cls, node):
        return f"{node['name']['firstName']} {node['name']['lastName']}"

    @classmethod
    def get_description(cls, node):
        return cls.parse_profile_information(node, "researchinterests")

    @classmethod
    def get_skills(cls, node):
        raw_skills = cls.parse_profile_information(node, "subjects")
        if not raw_skills:
            return []
        skills = strip_tags(raw_skills).split(",")
        return [skill.strip() for skill in skills]

    @classmethod
    def get_email(cls, node):
        staff_association = cls.get_legacy_valid_staff_organization_association(node)
        if not staff_association:
            return None
        for email in staff_association.get("emails", []):
            return email.get("value").get("value")
        return None

    @classmethod
    def get_is_employed(cls, node):
        staff_association = cls.get_legacy_valid_staff_organization_association(node)
        return bool(staff_association)

    @classmethod
    def get_photo_url(cls, node):
        profile_photos = node.get("profilePhotos", [])
        if not profile_photos:
            return None
        return profile_photos[0]["url"]

    @classmethod
    def get_job_title(cls, node):
        association = cls.get_legacy_valid_staff_organization_association(node, required_attribute="jobDescription")
        if not association:
            return None
        job_title_object = association.get("jobDescription")
        if not job_title_object:
            return None
        elif "term" in job_title_object:
            job_title_object = job_title_object["term"]
        return job_title_object["text"][0]["value"]


OBJECTIVE = {
    # Essential keys for functioning of the system
    "@": "$.items",
    "state": lambda node: PersonDocument.States.ACTIVE,
    "set": lambda node: "buas:person",
    "external_id": "$.uuid",
    "provider": BuasPersonExtractProcessor.get_provider,
    # Generic metadata
    "skills": BuasPersonExtractProcessor.get_skills,
    "is_employed": BuasPersonExtractProcessor.get_is_employed,
    "job_title": BuasPersonExtractProcessor.get_job_title,
    # Author metadata
    "author.name": BuasPersonExtractProcessor.get_name,
    "author.first_name": "$.name.firstName",
    "author.last_name": "$.name.lastName",
    # Sensitive metadata
    "sensitive.email": BuasPersonExtractProcessor.get_email,
    "sensitive.description": BuasPersonExtractProcessor.get_description,
    "sensitive.photo_url": BuasPersonExtractProcessor.get_photo_url,
    # Research based metadata
    "researcher.title": BuasPersonExtractProcessor.get_job_title,
    "researcher.orcid": "$.orcid",
}


SEEDING_PHASES = [
    {
        "phase": "persons",
        "strategy": "initial",
        "batch_size": None,
        "retrieve_data": {
            "resource": "persons.buaspersonresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
