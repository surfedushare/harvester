from sources.utils.hbo_kennisbank import HBOKennisbankExtractor, build_objective, build_seeding_phases
from sources.models import GreeniOAIPMHResource


class GreeniExtractor(HBOKennisbankExtractor):
    source_slug = "greeni"


OBJECTIVE = build_objective(GreeniExtractor)


SEEDING_PHASES = build_seeding_phases(GreeniOAIPMHResource, OBJECTIVE)
