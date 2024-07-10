import logging
from urlobject import URLObject

from datagrowth.resources import HttpResource


logger = logging.getLogger("harvester")


class AnatomyToolOAIPMH(HttpResource):

    URI_TEMPLATE = "https://anatomytool.org/oai-pmh?from={}"
    PARAMETERS = {
        "verb": "ListRecords",
        "metadataPrefix": "nl_lom"
    }

    def send(self, method, *args, **kwargs):
        args = (args[1],)  # ignores set_specification input, we'll always use the default
        return super().send(method, *args, **kwargs)

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
        verbose_name = "Anatomy tool OAIPMH harvest"
        verbose_name_plural = "Anatomy tool OAIPMH harvests"
