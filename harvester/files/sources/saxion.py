from sources.utils.hbo_kennisbank import build_seeding_phases
from sources.models import SaxionOAIPMHResource
from files.sources.hbo_kennisbank import HBOKennisbankFileExtractor, build_objective


class SaxionFileExtractor(HBOKennisbankFileExtractor):
    source_slug = "saxion"


OBJECTIVE = build_objective(SaxionFileExtractor)


SEEDING_PHASES = build_seeding_phases(SaxionOAIPMHResource, OBJECTIVE)
