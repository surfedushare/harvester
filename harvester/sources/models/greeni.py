import logging

from django.conf import settings
from django.db import models
from urlobject import URLObject

from datagrowth.configuration import create_config
from datagrowth.processors import ExtractProcessor

from core.models import HarvestHttpResource
from sources.extraction.greeni import GreeniDataExtraction, GREENI_EXTRACTION_OBJECTIVE


logger = logging.getLogger("harvester")


class GreeniOAIPMHResourceManager(models.Manager):

    def extract_seeds(self, set_specification, latest_update):
        queryset = self.get_queryset().filter(
            set_specification=set_specification,
            since__date__gte=latest_update.date(),
            status=200,
            is_extracted=False
        )

        oaipmh_objective = {
            "@": GreeniDataExtraction.get_oaipmh_records,
            "external_id": GreeniDataExtraction.get_oaipmh_external_id,
            "state": GreeniDataExtraction.get_oaipmh_record_state
        }
        oaipmh_objective.update(GREENI_EXTRACTION_OBJECTIVE)
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


class GreeniOAIPMHResource(HarvestHttpResource):

    objects = GreeniOAIPMHResourceManager()

    URI_TEMPLATE = settings.SOURCES["greeni"]["endpoint"] + "/webopac/oai2.CSP?set={}&from={}" \
        if settings.SOURCES["greeni"]["endpoint"] else "/webopac/oai2.CSP?set={}&from={}"
    PARAMETERS = {
        "verb": "ListRecords",
        "metadataPrefix": "didl"
    }

    use_multiple_sets = True

    def variables(self, *args):
        # Here we're casting the last element of the URL variables to a date string,
        # because Greeni doesn't handle times with timezones and we don't want to pass a long dubious time strings,
        # with possibly vague bugs as a consequence
        variables = super().variables(*args)
        variables["url"] = list(variables["url"])
        variables["url"][-1] = variables["since"].strftime("%Y-%m-%d")
        return variables

    def next_parameters(self):
        content_type, soup = self.content
        resumption_token = soup.find("resumptionToken")
        if not resumption_token or not resumption_token.text:
            return {}
        return {
            "verb": "ListRecords",
            "resumptionToken": resumption_token.text
        }

    def create_next_request(self):
        next_request = super().create_next_request()
        if not next_request:
            return
        url = URLObject(next_request.get("url"))
        url = url.without_query().set_query_params(**self.next_parameters())
        next_request["url"] = str(url)
        return next_request

    class Meta:
        verbose_name = "Greeni OAIPMH harvest"
        verbose_name_plural = "Greeni OAIPMH harvests"
