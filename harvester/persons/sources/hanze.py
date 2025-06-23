import os
from datetime import datetime
from dateutil.parser import parse as date_parser

from django.utils.html import strip_tags

from sources.utils.pure import PureExtractor


class HanzePersonsExtractProcessor(PureExtractor):

    source_name = "Hanze"
    source_slug = "hanze"

    @classmethod
    def get_valid_staff_organization_association(cls, node, required_attribute=None):
        today = datetime.today()
        for association in node.get("staffOrganizationAssociations", []):
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
    def parse_profile_information(cls, node, info_type):
        texts = []
        for profile_information in node.get("profileInformation", []):
            profile_information_uri = profile_information.get("type").get("uri")
            _, profile_information_type = os.path.split(profile_information_uri)
            if profile_information_type == info_type:
                text = profile_information.get("value")
                if text is None:
                    continue
                texts.append(text.get("nl_NL", next(iter(text.values()))))
        return texts

    @classmethod
    def get_name(cls, node):
        return f"{node['name']['firstName']} {node['name']['lastName']}"

    @classmethod
    def get_skills(cls, node):
        skills = []
        for groups in node.get("keywordGroups", []):
            for container in groups.get("keywordContainers", []):
                for keyword_object in container.get("freeKeywords", []):
                    skills += keyword_object.get("freeKeywords", [])
        return skills

    @classmethod
    def get_description(cls, node):
        description_types = [
            "personal_profile",
            "researchinterests",
            "teaching",
            "url",
            "professionalinformation",
            "intellectualproperty",
        ]
        profile_descriptions = []
        for description_type in description_types:
            descriptions = []
            raw_descriptions = cls.parse_profile_information(node, description_type)
            if not raw_descriptions:
                continue
            for description in raw_descriptions:
                clean_description = strip_tags(description)
                descriptions.append(clean_description)
            profile_descriptions.append("\n".join(descriptions))
        # Add academic qualifications as a list of titles
        academic_qualifications = []
        for qualification in node.get("academicQualifications", []):
            if "qualification" not in qualification:
                continue
            texts = qualification["qualification"].get("term")
            if not texts:
                continue
            academic_qualification = texts.get("nl_NL", next(iter(texts.values())))
            academic_qualifications.append(academic_qualification)
        if academic_qualifications:
            profile_descriptions.append("\n".join(academic_qualifications))
        # Merge profile information with academic qualifications
        return "\n\n".join(profile_descriptions) if profile_descriptions else None

    @classmethod
    def get_isni(cls, node):
        isni_identifier = next(
            (identifier for identifier in node.get("identifiers", [])
             if "isni" in identifier.get("type", {}).get("uri", "")),
            None
        )
        return isni_identifier["id"] if isni_identifier else None

    @classmethod
    def get_is_employed(cls, node):
        today = datetime.today()
        for association in node.get("staffOrganizationAssociations", []):
            end_date = association["period"].get("endDate", None)
            if not end_date or date_parser(end_date) > today:
                break
        else:
            return False
        return True

    @classmethod
    def get_photo_url(cls, node):
        photo_list = node.get("profilePhotos", None)
        if not photo_list:
            return
        photo_url = photo_list[0].get("url", None)
        if not photo_url:
            return
        file_path_segment = "/nppo/"
        if file_path_segment not in photo_url:
            return photo_url  # not dealing with a url we recognize as a file url
        start = photo_url.index(file_path_segment)
        file_path = photo_url[start + len(file_path_segment):]
        return cls._parse_file_url(file_path)

    @classmethod
    def get_job_title(cls, node):
        association = cls.get_valid_staff_organization_association(node, required_attribute="jobTitle")
        if not association:
            return
        job_title_object = association.get("jobTitle", None)
        if not job_title_object:
            return
        return next(iter(job_title_object["term"].values()), None)

    @classmethod
    def get_phone(cls, node):
        association = cls.get_valid_staff_organization_association(node)
        if not association:
            return
        phone_numbers = association.get("phoneNumbers", [])
        if not phone_numbers:
            return
        return phone_numbers[0]["value"]

    @classmethod
    def get_socials(cls, node):
        raw_links = node.get("links", [])
        links = []
        for raw_link in raw_links:
            raw_link_type = raw_link.get("linkType")
            if not raw_link_type:
                continue
            _, link_type = os.path.split(raw_link_type["uri"])
            url = raw_link["url"]
            links.append({"type": link_type, "url": url})
        return links


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$.items",
    "external_id": "$.uuid",
    "user_id": "$.user.uuid",
    "state": lambda node: "active",
    "set": lambda node: "hanze:person",
    "provider": HanzePersonsExtractProcessor.get_provider,
    # Generic metadata
    "skills": HanzePersonsExtractProcessor.get_skills,
    "is_employed": HanzePersonsExtractProcessor.get_is_employed,
    "job_title": HanzePersonsExtractProcessor.get_job_title,
    # Author metadata
    "author.name": HanzePersonsExtractProcessor.get_name,
    "author.first_name": "$.name.firstName",
    "author.last_name": "$.name.lastName",
    "author.isni": HanzePersonsExtractProcessor.get_isni,
    # Sensitive metadata
    "sensitive.phone": HanzePersonsExtractProcessor.get_phone,
    "sensitive.description": HanzePersonsExtractProcessor.get_description,
    "sensitive.photo_url": HanzePersonsExtractProcessor.get_photo_url,
    "sensitive.socials": HanzePersonsExtractProcessor.get_socials,
    # Research based metadata
    "researcher.orcid": "$.orcid",
}


SEEDING_PHASES = [
    {
        "phase": "persons",
        "strategy": "initial",
        "batch_size": 100,
        "retrieve_data": {
            "resource": "persons.hanzepersonresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    },
    {
        "phase": "emails",
        "strategy": "merge",
        "batch_size": None,
        "retrieve_data": {
            "resource": "persons.hanzeuserresource",
            "method": "get",
            "args": ["$.user_id"],
            "kwargs": {},
        },
        "contribute_data": {
            "merge_on": "user_id",
            "objective": {
                "@": "$",
                "user_id": "$.uuid",
                "sensitive.email": "$.email"
            }
        }
    }
]
