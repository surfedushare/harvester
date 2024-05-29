import logging

from django.conf import settings

from core.models import HarvestHttpResource


logger = logging.getLogger("harvester")


class SaxionOAIPMHResource(HarvestHttpResource):

    URI_TEMPLATE = settings.SOURCES["saxion"]["endpoint"] + "/harvester?set={}&from={}" \
        if settings.SOURCES["saxion"]["endpoint"] else "/harvester?set={}&from={}"
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
