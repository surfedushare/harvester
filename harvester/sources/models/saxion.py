import logging

from django.conf import settings
from django.db import models

from datagrowth.configuration import create_config
from datagrowth.processors import ExtractProcessor

from core.models import HarvestHttpResource
from sources.extraction.saxion import SaxionDataExtraction, SAXION_EXTRACTION_OBJECTIVE


logger = logging.getLogger("harvester")


class SaxionOAIPMHResourceManager(models.Manager):

    def extract_seeds(self, set_specification, latest_update):
        queryset = self.get_queryset().filter(
            set_specification=set_specification,
            since__date__gte=latest_update.date(),
            status=200,
            is_extracted=False
        )

        oaipmh_objective = {
            "@": SaxionDataExtraction.get_oaipmh_records,
            "external_id": SaxionDataExtraction.get_oaipmh_external_id,
            "state": SaxionDataExtraction.get_oaipmh_record_state
        }
        oaipmh_objective.update(SAXION_EXTRACTION_OBJECTIVE)
        extract_config = create_config("extract_processor", {
            "objective": oaipmh_objective
        })
        prc = ExtractProcessor(config=extract_config)

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


class SaxionOAIPMHResource(HarvestHttpResource):

    objects = SaxionOAIPMHResourceManager()

    URI_TEMPLATE = settings.SOURCES["saxion"]["endpoint"] + "/harvester?set={}" \
        if settings.SOURCES["saxion"]["endpoint"] else "/harvester?set={}"
    PARAMETERS = {
        "verb": "ListRecords",
        "metadataPrefix": "oai_mods"
    }

    def next_parameters(self):
        content_type, soup = self.content
        resumption_token = soup.find("resumptionToken")
        if not resumption_token or not resumption_token.text:
            return {}
        return {
            "resumptionToken": resumption_token.text
        }

    class Meta:
        verbose_name = "Saxion OAIPMH harvest"
        verbose_name_plural = "Saxion OAIPMH harvests"
