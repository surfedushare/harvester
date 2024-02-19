from sources.utils.hbo_kennisbank import HBOKennisbankExtractor, build_objective, build_seeding_phases
from sources.models import SaxionOAIPMHResource


class SaxionExtractor(HBOKennisbankExtractor):
    source_slug = "saxion"


OBJECTIVE = build_objective(SaxionExtractor)


SEEDING_PHASES = build_seeding_phases(SaxionOAIPMHResource, OBJECTIVE)
