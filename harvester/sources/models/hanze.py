from django.conf import settings
from django.db import models

from datagrowth.configuration import create_config

from core.models import HarvestHttpResource
from sources.extraction.hanze import HanzeResourceObjectExtraction


class HanzeResearchObjectResourceManager(models.Manager):

    def extract_seeds(self, latest_update):
        latest_update = latest_update.replace(microsecond=0)
        queryset = self.get_queryset().filter(
            since__gte=latest_update,
            status=200,
            is_extracted=False
        )

        metadata_objective = {
            "@": "$.items",
            "external_id": "$.uuid",
            "state": HanzeResourceObjectExtraction.get_record_state
        }
        metadata_objective.update(HanzeResourceObjectExtraction.OBJECTIVE)
        extract_config = create_config("extract_processor", {
            "objective": metadata_objective
        })
        prc = HanzeResourceObjectExtraction(config=extract_config)

        results = []
        for harvest in queryset:
            seed_resource = {
                "resource": f"{harvest._meta.app_label}.{harvest._meta.model_name}",
                "id": harvest.id,
                "success": True
            }
            for seed in prc.extract_from_resource(harvest):
                seed["seed_resource"] = seed_resource
                results.append(seed)
        return results


class HanzeResearchObjectResource(HarvestHttpResource):

    objects = HanzeResearchObjectResourceManager()

    set_specification = models.CharField(max_length=255, blank=True, null=False, default="hanze")
    use_multiple_sets = False

    URI_TEMPLATE = "https://hanzetest.azure-api.net/nppo/research-outputs"
    PARAMETERS = {
        "size": 500,
        "offset": 0
    }

    def send(self, method, *args, **kwargs):
        args = (args[1],)  # ignores set_specification input, we'll always use the default
        return super().send(method, *args, **kwargs)

    def auth_headers(self):
        return {
            "Ocp-Apim-Subscription-Key": settings.HANZE_API_KEY
        }

    def next_parameters(self):
        content_type, data = self.content
        count = data["count"]
        page_info = data["pageInformation"]
        next_offset = page_info["offset"] + page_info["size"]
        if next_offset >= count:
            return {}
        return {
            "offset": next_offset
        }
