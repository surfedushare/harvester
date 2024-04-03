from sources.utils.pure import build_seeding_phases
from sources.models import HanzeResearchObjectResource
from products.sources.pure import PureProductExtraction, build_objective


class HanzeProductExtractor(PureProductExtraction):
    pure_api_prefix = "/nppo/"
    source_slug = "hanze"
    support_subtitle = True


OBJECTIVE = build_objective(HanzeProductExtractor, "hanze:hanze")


SEEDING_PHASES = build_seeding_phases(HanzeResearchObjectResource, OBJECTIVE)
