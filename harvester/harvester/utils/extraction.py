import logging

from django.conf import settings
from django.apps import apps


logger = logging.getLogger("harvester")


NPPO_PUBLISHERS_WHITELIST = {
    "Hogeschool Utrecht",
    "Fontys",
    "Hogeschool Rotterdam",
    "Zuyd Hogeschool",
    "Hogeschool van Arnhem en Nijmegen",
}


def get_harvest_seeds(repository, set_specification, latest_update, include_deleted=True, include_no_url=False):
    """
    Extracts metadata from HarvestHttpResource

    Currently supports Sharekit and Edurep
    More information on Edurep: https://developers.wiki.kennisnet.nl/index.php/Edurep:Hoofdpagina
    """
    RepositoryResource = apps.get_model(repository)
    if RepositoryResource.use_multiple_sets:
        results = RepositoryResource.objects.extract_seeds(set_specification, latest_update)
    else:
        results = RepositoryResource.objects.extract_seeds(latest_update)

    seeds = []
    for seed in results:
        # In many cases it doesn't make sense to try and process files without a URL
        # So by default we skip these seeds,
        # but some seeds that group together materials do not have files/URLs and you can include these
        if seed["state"] == "active" and not seed["url"] and not include_no_url:
            continue
        seeds.append(seed)
    # Now we'll mark any invalid seeds as deleted to make sure they disappear
    # Invalid seeds have a copyright or are of insufficient education level
    for seed in seeds:
        if not seed["copyright"] or seed["copyright"] in ["yes", "unknown"]:
            seed["state"] = "deleted"
        if seed["lowest_educational_level"] < 2 and settings.PROJECT == "edusources":  # lower level than HBO
            seed["state"] = "deleted"
        if seed.get("is_restricted", False):
            seed["analysis_allowed"] = False
    # And we return the seeds based on whether to include deleted or not
    return seeds if include_deleted else \
        [result for result in seeds if result.get("state", "active") == "active"]
