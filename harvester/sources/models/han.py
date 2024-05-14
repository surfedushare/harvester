import logging

from django.conf import settings
from urlobject import URLObject

from core.models import HarvestHttpResource


logger = logging.getLogger("harvester")


class HanOAIPMHResource(HarvestHttpResource):

    URI_TEMPLATE = settings.SOURCES["han"]["endpoint"] + "/hanoai/request?set={}&from={}" \
        if settings.SOURCES["han"]["endpoint"] else "/hanoai/request?set={}&from={}"
    PARAMETERS = {
        "verb": "ListRecords",
        "metadataPrefix": "nl_didl"
    }

    use_multiple_sets = True

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
        verbose_name = "HAN OAIPMH harvest"
        verbose_name_plural = "HAN OAIPMH harvests"
