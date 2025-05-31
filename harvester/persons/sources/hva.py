import os
from datetime import datetime
from dateutil.parser import parse as date_parser

from sources.utils.pure import PureExtractor


class HvaPersonsExtractProcessor(PureExtractor):

    pure_api_prefix = "/ws/api/"
    source_name = "Hogeschool van Amsterdam"
    source_slug = "hva"

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
    def get_job_title(cls, node):
        association = cls.get_valid_staff_organization_association(node, required_attribute="jobTitle")
        if not association:
            return
        job_title_object = association.get("jobTitle", None)
        if not job_title_object:
            return
        return next(iter(job_title_object["term"].values()), None)


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$.items",
    "external_id": "$.uuid",
    "user_id": "$.user.uuid",
    "state": lambda node: "active",
    "set": lambda node: "hva:person",
    "provider": HvaPersonsExtractProcessor.get_provider,
    # Generic metadata
    "is_employed": HvaPersonsExtractProcessor.get_is_employed,
    "job_title": HvaPersonsExtractProcessor.get_job_title,
    # Author metadata
    "author.name": HvaPersonsExtractProcessor.get_name,
    "author.first_name": "$.name.firstName",
    "author.last_name": "$.name.lastName",
    "author.isni": HvaPersonsExtractProcessor.get_isni,
    # Research based metadata
    "researcher.orcid": "$.orcid",
}


SEEDING_PHASES = [
    {
        "phase": "persons",
        "strategy": "initial",
        "batch_size": 100,
        "retrieve_data": {
            "resource": "persons.hvapersonresource",
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
            "resource": "persons.hvauserresource",
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
