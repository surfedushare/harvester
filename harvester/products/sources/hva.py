from sources.utils.pure import build_seeding_phases
from sources.models import HvaPureResource
from products.sources.pure import PureProductExtraction, build_objective


class HvAProductExtractor(PureProductExtraction):
    pass


OBJECTIVE = build_objective(HvAProductExtractor, "hva:hva")


SEEDING_PHASES = build_seeding_phases(HvaPureResource, OBJECTIVE)
