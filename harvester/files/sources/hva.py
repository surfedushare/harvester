from sources.utils.pure import build_seeding_phases
from sources.models import HvaPureResource
from files.sources.pure import PureFileExtraction, build_objective


class HvAFileExtractor(PureFileExtraction):
    pure_api_prefix = "/ws/api/"
    source_slug = "hva"


OBJECTIVE = build_objective(HvAFileExtractor, "hva:hva")


SEEDING_PHASES = build_seeding_phases(HvaPureResource, OBJECTIVE)
