from sources.utils.hbo_kennisbank import HBOKennisbankExtractor, build_objective, build_seeding_phases
from sources.models import GreeniOAIPMHResource


class GreeniExtractor(HBOKennisbankExtractor):
    source_slug = "greeni"

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


OBJECTIVE = build_objective(GreeniExtractor)


SEEDING_PHASES = build_seeding_phases(GreeniOAIPMHResource, OBJECTIVE)
