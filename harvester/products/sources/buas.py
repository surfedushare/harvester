from sources.utils.pure import build_seeding_phases
from sources.models import BuasPureResource
from products.sources.pure import PureProductExtraction, build_objective


class BuasProductExtractor(PureProductExtraction):
    source_slug = "buas"
    source_name = "Breda University of Applied Sciences"
    authors_property = "personAssociations"
    file_url_property = "fileURL"

    @classmethod
    def get_keywords(cls, node):
        results = []
        for keywords in node.get("keywordGroups", []):
            match keywords["logicalName"]:
                case "keywordContainers":
                    for container in keywords["keywordContainers"]:
                        for free_keywords in container["freeKeywords"]:
                            results += free_keywords.get("freeKeywords", [])
        return results


OBJECTIVE = build_objective(BuasProductExtractor, "buas:buas")


SEEDING_PHASES = build_seeding_phases(BuasPureResource, OBJECTIVE)
