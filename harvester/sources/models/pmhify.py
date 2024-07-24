from urlobject import URLObject

from datagrowth.resources import HttpResource


class PmhifyOAIPMHResource(HttpResource):

    URI_TEMPLATE = "https://dev.pmhify.edusources.nl/endpoint/{}/oai-pmh/"
    PARAMETERS = {
        "verb": "ListRecords",
        "metadataPrefix": "nl_LOM"
    }

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
        verbose_name = "PMHIFY OAIPMH resource"
        verbose_name_plural = "PMHIFY OAIPMH resources"
