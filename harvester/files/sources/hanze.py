from django.conf import settings

from sources.utils.pure import build_seeding_phases
from sources.models import HanzeResearchObjectResource
from files.sources.pure import PureFileExtraction, build_objective


class HanzeFileExtractor(PureFileExtraction):
    source_slug = "hanze"
    source_name = "Hanze"

    @classmethod
    def parse_file_url(cls, url):
        hanze_middleware_endpoint = f"{settings.SOURCES["hanze"]["endpoint"]}/nppo/"
        return url.replace("https://research.hanze.nl/ws/api/", hanze_middleware_endpoint)


OBJECTIVE = build_objective(HanzeFileExtractor, "hanze:hanze")


SEEDING_PHASES = build_seeding_phases(HanzeResearchObjectResource, OBJECTIVE)
