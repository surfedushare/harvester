from sources.utils.pure import build_seeding_phases
from sources.models import HanzeResearchObjectResource
from files.sources.pure import PureFileExtraction, build_objective


class HanzeFileExtractor(PureFileExtraction):
    pure_api_prefix = "/nppo/"
    source_slug = "hanze"
    source_name = "Hanze"


OBJECTIVE = build_objective(HanzeFileExtractor, "hanze:hanze")


SEEDING_PHASES = build_seeding_phases(HanzeResearchObjectResource, OBJECTIVE)
