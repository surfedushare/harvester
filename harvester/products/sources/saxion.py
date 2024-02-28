from sources.utils.hbo_kennisbank import build_seeding_phases
from sources.models import SaxionOAIPMHResource
from products.sources.hbo_kennisbank import HBOKennisbankProductExtractor, build_objective


class SaxionProductExtractor(HBOKennisbankProductExtractor):
    source_slug = "saxion"


OBJECTIVE = build_objective(SaxionProductExtractor)


SEEDING_PHASES = build_seeding_phases(SaxionOAIPMHResource, OBJECTIVE)
