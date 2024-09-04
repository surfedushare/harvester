import os
from urlobject import URLObject
from collections import defaultdict

from django.contrib.auth.models import User

from core.models import MatomoVisitsResource, Query, QueryRanking
from search.clients import get_search_client


def _create_or_increase_query_ranking(search_client, dataset_version, query_string, url_object, user):
    from core.models import Document
    _, external_id = os.path.split(url_object.path.strip("/"))
    external_id = search_client.clean_external_id(external_id)
    document = Document.objects.filter(dataset_version=dataset_version, reference=external_id).last()
    if not document:
        return external_id
    language = document.get_analyzer_language() or "unk"
    query, _ = Query.objects.get_or_create(query=query_string)
    ranking, _ = QueryRanking.objects.get_or_create(query=query, user=user)
    alias = f"edusources-{language}"
    ranking_key = f"{alias}:{external_id}"
    if ranking_key not in ranking.ranking:
        ranking.ranking[ranking_key] = 1
    else:
        ranking.ranking[ranking_key] += 1
    ranking.save()


def create_or_update_download_query_rankings():
    from core.models import DatasetVersion
    latest_dataset_version = DatasetVersion.objects.get_current_version()
    download_event_filter = {
        "Goal.Download": True
    }
    superuser = User.objects.get(username="supersurf")
    search_client = get_search_client()
    not_found = defaultdict(int)
    visit_lengths = defaultdict(int)
    visitor_id_counts = defaultdict(int)
    for visit in MatomoVisitsResource.objects.iterate_visits(filter_custom_events=download_event_filter, min_actions=3):
        visitor_id_counts[visit["visitorId"]] += 1
    for visit in MatomoVisitsResource.objects.iterate_visits(filter_custom_events=download_event_filter, min_actions=3):
        current_query = None
        current_result = None
        visit_lengths[len(visit["actionDetails"])] += 1
        for action in visit["actionDetails"]:
            if action["type"] == "search":  # record when a query was made and continue iterating
                current_query = action["siteSearchKeyword"] if not action["siteSearchCategory"] else None
                continue
            if not current_query:  # ignore everything when no search has been done or people clicked away after search
                continue
            url = URLObject(action["url"])
            is_result = "mater" in url.path  # either /materiaal or /en/materials
            if is_result and not current_result:
                current_result = action["url"]
                continue
            elif is_result and action.get("eventAction", None) == "Download":  # record a hit
                missing = _create_or_increase_query_ranking(search_client, latest_dataset_version, current_query, url,
                                                            superuser)
                if missing:
                    not_found[missing] += 1
                current_result = None
                continue
            # Non-search related click to a material/other page or immediately after hit
            # We'll reset state
            current_query = None
            current_result = None
    return not_found, visit_lengths
