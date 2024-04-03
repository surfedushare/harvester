from sources.utils.pure import build_seeding_phases
from sources.models import HanzeResearchObjectResource
from sources.extraction.hanze.research_themes import ASJC_TO_RESEARCH_THEME
from products.sources.pure import PureProductExtraction, build_objective


class HanzeProductExtractor(PureProductExtraction):

    pure_api_prefix = "/nppo/"
    source_slug = "hanze"
    support_subtitle = True

    @classmethod
    def get_keywords(cls, node):
        results = []
        for keywords in node.get("keywordGroups", []):
            match keywords["logicalName"]:
                case "keywordContainers":
                    for free_keywords in keywords["keywords"]:
                        results += free_keywords["freeKeywords"]
                case "ASJCSubjectAreas":
                    for classification in keywords["classifications"]:
                        results.append(classification["term"]["en_GB"])
                case "research_focus_areas":
                    for classification in keywords["classifications"]:
                        if classification["uri"] == "research_focus_areas/05/no_hanze_research_focus_area_applicable":
                            continue
                        elif classification["uri"] == "research_focus_areas/02g_no_research_line_applicable":
                            continue
                        results.append(classification["term"]["en_GB"])
        return list(set(results))

    @classmethod
    def get_research_themes(cls, node):
        research_themes = []
        for keywords in node.get("keywordGroups", []):
            if keywords["logicalName"] == "ASJCSubjectAreas":
                asjc_identifiers = [
                    classification["uri"].replace("/dk/atira/pure/subjectarea/asjc/", "")
                    for classification in keywords["classifications"]
                ]
                research_themes += [ASJC_TO_RESEARCH_THEME[identifier] for identifier in asjc_identifiers]
        return research_themes


OBJECTIVE = build_objective(HanzeProductExtractor, "hanze:hanze")


SEEDING_PHASES = build_seeding_phases(HanzeResearchObjectResource, OBJECTIVE)
