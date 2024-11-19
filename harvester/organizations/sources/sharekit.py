from sources.utils.sharekit import SharekitExtractor


class SharekitOrganizationExtraction:

    @classmethod
    def get_record_state(cls, node):
        state = SharekitExtractor.extract_state(node)
        return state if not node["attributes"].get("inactive") == 1 else "deleted"

    @classmethod
    def get_channel(cls, data):
        return SharekitExtractor.extract_channel(data)

    #############################
    # Organization
    #############################

    @classmethod
    def get_parents(cls, node):
        if not (parent := node["attributes"].get("parentName")):
            return []
        return [parent]


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": "$.data",
    "state": SharekitOrganizationExtraction.get_record_state,
    "external_id": "$.id",
    "#set": SharekitOrganizationExtraction.get_channel,
    "provider": lambda node: {"name": "SURFSharekit"},
    # Generic metadata
    "name": "$.attributes.name",
    "description": "$.attributes.description",
    "ror": "$.attributes.ror",
    "type": "$.attributes.level",
    "secretary": lambda node: False,
    "parents": SharekitOrganizationExtraction.get_parents,
}


SEEDING_PHASES = [
    {
        "phase": "organizations",
        "strategy": "initial",
        "batch_size": 25,
        "retrieve_data": {
            "resource": "organizations.sharekitorganizationresource",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
