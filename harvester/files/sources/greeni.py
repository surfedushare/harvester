from sources.utils.hbo_kennisbank import build_seeding_phases
from sources.models import GreeniOAIPMHResource
from files.sources.hbo_kennisbank import HBOKennisbankFileExtractor, build_objective, back_fill_deletes


class GreeniFileExtractor(HBOKennisbankFileExtractor):

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


OBJECTIVE = build_objective(GreeniFileExtractor)


SEEDING_PHASES = build_seeding_phases(GreeniOAIPMHResource, OBJECTIVE, back_fill_deletes=back_fill_deletes)
