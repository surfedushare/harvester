import logging
from dateutil.parser import parse as parse_date_string

from django.conf import settings
from django.utils.timezone import make_aware, is_aware
from urlobject import URLObject

from datagrowth.resources import HttpResource


logger = logging.getLogger("harvester")


class GreeniOAIPMHResource(HttpResource):

    URI_TEMPLATE = settings.SOURCES["greeni"]["endpoint"] + "/webopac/oai2.CSP?set={}&from={}" \
        if settings.SOURCES["greeni"]["endpoint"] else "/webopac/oai2.CSP?set={}&from={}"
    PARAMETERS = {
        "verb": "ListRecords",
        "metadataPrefix": "didl"
    }

    def variables(self, *args):
        # Here we're casting the last element of the URL variables to a date string,
        # because Greeni doesn't handle times with timezones and we don't want to pass along dubious time strings,
        # with possibly vague bugs as a consequence
        variables = super().variables(*args)
        # Use the last element of the url variables as a since_time
        since_time = None
        if len(variables["url"]) == 2:
            since_time = variables["url"][1]
        elif len(variables["url"]) == 1:
            since_time = variables["url"][0]
        # Validate that this is indeed a datetime and not str
        if isinstance(since_time, str):
            since_time = parse_date_string(since_time)
            if not is_aware(since_time):
                since_time = make_aware(since_time)
        # Manipulate the returned variables to a date string that Greeni can handle
        variables["url"] = list(variables["url"])
        variables["url"][-1] = since_time.strftime("%Y-%m-%d")
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
