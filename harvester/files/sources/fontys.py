from sources.utils.pure import build_seeding_phases
from sources.models import FontysPureResource
from files.sources.pure import PureFileExtraction, build_objective


class FontysFileExtractor(PureFileExtraction):
    source_slug = "fontys"


OBJECTIVE = build_objective(FontysFileExtractor, "fontys:fontys")


SEEDING_PHASES = build_seeding_phases(FontysPureResource, OBJECTIVE)
