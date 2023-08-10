class Repositories:
    EDUREP_JSONSEARCH = "sources.EdurepJsonSearchResource"
    EDUREP = "edurep.EdurepOAIPMH"
    SHAREKIT = "sharekit.SharekitMetadataHarvest"
    ANATOMY_TOOL = "anatomy_tool.AnatomyToolOAIPMH"
    HANZE = "sources.HanzeResearchObjectResource"
    HAN = "sources.HanOAIPMHResource"
    HVA = "sources.HvaPureResource"
    HKU = "sources.HkuMetadataResource"
    GREENI = "sources.GreeniOAIPMHResource"
    BUAS = "sources.BuasPureResource"
    PUBLINOVA = "sources.PublinovaMetadataResource"
    SAXION = "sources.SaxionOAIPMHResource"


def get_repository_id(repository_resource):
    repository_id = next(
        (choice[1] for choice in REPOSITORY_CHOICES if choice[0] == repository_resource),
        None
    )
    if repository_id is None:
        return
    return repository_id.lower()


REPOSITORY_CHOICES = [
    (value, attr.lower().capitalize())
    for attr, value in sorted(Repositories.__dict__.items()) if not attr.startswith("_")
]


class DeletePolicies:
    """
    Details: http://www.openarchives.org/OAI/openarchivesprotocol.html#DeletedRecords
    """
    NO = "no"
    PERSISTENT = "persistent"
    TRANSIENT = "transient"


DELETE_POLICY_CHOICES = [
    (value, attr.lower().capitalize())
    for attr, value in sorted(DeletePolicies.__dict__.items()) if not attr.startswith("_")
]


class HarvestStages:
    NEW = "New"
    BASIC = "Basic"
    VIDEO = "Video"
    PREVIEW = "Preview"
    COMPLETE = "Complete"


HARVEST_STAGE_CHOICES = [
    (value, value) for attr, value in sorted(HarvestStages.__dict__.items()) if not attr.startswith("_")
]


HIGHER_EDUCATION_LEVELS = {
    "BVE": 1,
    "HBO": 2,
    "HBO - Bachelor": 2,
    "HBO - Master": 2,
    "WO": 3,
    "WO - Bachelor": 3,
    "WO - Master": 3,
}


SITE_SHORTHAND_BY_DOMAIN = {
    "harvester.prod.surfedushare.nl": "edusources",
    "harvester.mbo.prod.surfedushare.nl": "mbo",
    "harvester.publinova.nl": "publinova",
}
