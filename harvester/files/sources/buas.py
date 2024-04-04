from sources.utils.pure import build_seeding_phases
from sources.models import BuasPureResource
from files.sources.pure import PureFileExtraction, build_objective


class BuasFileExtractor(PureFileExtraction):
    source_slug = "buas"
    file_url_property = "fileURL"


OBJECTIVE = build_objective(BuasFileExtractor, "buas:buas")


SEEDING_PHASES = build_seeding_phases(BuasPureResource, OBJECTIVE)
