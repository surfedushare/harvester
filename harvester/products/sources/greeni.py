from sources.utils.hbo_kennisbank import build_seeding_phases
from sources.models import GreeniOAIPMHResource
from products.sources.hbo_kennisbank import HBOKennisbankProductExtractor, build_objective


class GreeniProductExtractor(HBOKennisbankProductExtractor):
    source_slug = "greeni"

    @classmethod
    def get_oaipmh_record_state(cls, soup, el):
        state = super().get_oaipmh_record_state(soup, el)
        metadata = el.find("metadata")
        if metadata and metadata.string and not metadata.string.strip():  # detects an empty (non-self-closing) element
            state = "inactive"
        return state

    @classmethod
    def get_oaipmh_set(cls, soup):
        oaipmh_set = super().get_oaipmh_set(soup)
        if oaipmh_set:
            return oaipmh_set
        request = soup.find("request")
        resumption_token = request.get("resumptionToken", "").strip()
        set_specification = resumption_token.split("|")[0]
        if not set_specification:
            return
        return f"{cls.source_slug}:{set_specification}"


OBJECTIVE = build_objective(GreeniProductExtractor)


SEEDING_PHASES = build_seeding_phases(GreeniOAIPMHResource, OBJECTIVE)
