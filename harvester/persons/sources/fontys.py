import os
from datetime import datetime
from dateutil.parser import parse as date_parser

from sources.utils.pure import PureExtractor


class FontysPersonsExtractProcessor(PureExtractor):

    source_name = "Fontys Hogescholen"
    source_slug = "fontys"

    @classmethod
    def get_valid_staff_organization_association(cls, node, required_attribute=None):
        today = datetime.today()
        for association in node.get("staffOrganizationAssociations", []):
            end_date = association.get("period", {}).get("endDate", None)
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
            profile_information_uri = profile_information.get("type", {}).get("uri", "")
            _, profile_information_type = os.path.split(profile_information_uri)
            if profile_information_type == info_type:
                text = profile_information.get("value")
                if text is None:
                    continue
                texts.append(text.get("nl_NL", next(iter(text.values()))))
        return texts

    @classmethod
    def get_name(cls, node):
        first_name = node.get("name", {}).get("firstName", "")
        last_name = node.get("name", {}).get("lastName", "")
        return f"{first_name} {last_name}".strip()

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
            end_date = association.get("period", {}).get("endDate", None)
            if not end_date or date_parser(end_date, ignoretz=True) > today:
                break
        else:
            return False
        return True

    @classmethod
    def get_email(cls, node):
        association = cls.get_valid_staff_organization_association(node)
        if not association:
            return None
        for email in association.get("emails", []):
            return email.get("value")
        return None

    @classmethod
    def get_job_title(cls, node):
        association = cls.get_valid_staff_organization_association(node, required_attribute="jobTitle")
        if not association:
            return
        job_title_object = association.get("jobTitle")
        if not job_title_object:
            return
        term = job_title_object.get("term", {})
        return term.get("nl_NL", term.get("en_GB"))


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$.items",
    "external_id": "$.uuid",
    "state": lambda node: "active",
    "set": lambda node: "fontys:person",
    "provider": FontysPersonsExtractProcessor.get_provider,
    # Generic metadata
    "is_employed": FontysPersonsExtractProcessor.get_is_employed,
    "job_title": FontysPersonsExtractProcessor.get_job_title,
    # Author metadata
    "author.name": FontysPersonsExtractProcessor.get_name,
    "author.first_name": "$.name.firstName",
    "author.last_name": "$.name.lastName",
    "author.isni": FontysPersonsExtractProcessor.get_isni,
    # Sensitive metadata
    "sensitive.email": FontysPersonsExtractProcessor.get_email,
    # Research based metadata
    "researcher.orcid": "$.orcid",
}


SEEDING_PHASES = [
    {
        "phase": "persons",
        "strategy": "initial",
        "batch_size": 100,
        "retrieve_data": {
            "resource": "persons.fontyspersonresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
