import logging

from django.conf import settings
from urlobject import URLObject

from core.models import HarvestHttpResource


logger = logging.getLogger("harvester")


class GreeniOAIPMHResource(HarvestHttpResource):

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
