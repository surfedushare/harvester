import os
from urlobject import URLObject

from django.contrib.auth.models import User

from core.models import DatasetVersion, MatomoVisitsResource, Query, QueryRanking, Document


def _create_or_increase_query_ranking(dataset_version, query_string, url_object, user):
    _, external_id = os.path.split(url_object.path.strip("/"))
    document = Document.objects.filter(dataset_version=dataset_version, reference=external_id).last()
    if not document:
        print(f"Skipping: {external_id}")
        return
    language = document.get_language() or "unk"
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
    latest_dataset_version = DatasetVersion.objects.get_current_version()
    download_event_filter = {
        "Goal.Download": True
    }
    superuser = User.objects.get(username="supersurf")
    for visit in MatomoVisitsResource.objects.iterate_visits(filter_custom_events=download_event_filter, min_actions=3):
        current_query = None
        current_result = None
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
                _create_or_increase_query_ranking(latest_dataset_version, current_query, url, superuser)
            # Non-search related click to a material/other page or immediately after hit
            # We'll reset state
            current_query = None
            current_result = None
