from sources.utils.pure import build_seeding_phases
from sources.models import FontysPureResource
from products.sources.pure import PureProductExtraction, build_objective


class FontysProductExtractor(PureProductExtraction):
    source_slug = "fontys"
    source_name = "Fontys Hogescholen"


OBJECTIVE = build_objective(FontysProductExtractor, "fontys:fontys")


SEEDING_PHASES = build_seeding_phases(FontysPureResource, OBJECTIVE)
