import os
import factory
from datetime import datetime
from urllib.parse import quote

from django.conf import settings
from django.utils.timezone import make_aware

from sources.models import SaxionOAIPMHResource


uri = SaxionOAIPMHResource.URI_TEMPLATE.replace("https://", "")
start_params = uri.find("?")
ENDPOINT = uri[:start_params]
RESUMPTION_TOKEN = "5608392947620842476"


def since(is_initial) -> str:
    if is_initial:
        date = make_aware(datetime(year=1970, month=1, day=1))
    else:
        date = make_aware(datetime(year=2020, month=1, day=1))
    return f"{date:%Y-%m-%dT%H:%M:%SZ}"


class SaxionOAIPMHResourceFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = SaxionOAIPMHResource
        strategy = factory.BUILD_STRATEGY

    class Params:
        is_initial = True
        number = 0
        resumption = None

    status = 200
    head = {
        "content-type": "text/xml"
    }

    @factory.lazy_attribute
    def uri(self):
        from_param = quote(since(self.is_initial))
        identity = f"from={from_param}&metadataPrefix=oai_mods"
        if self.resumption:
            identity += f"&resumptionToken={quote(self.resumption)}"
        identity += "&set=kenniscentra"
        return f"{ENDPOINT}?{identity}&verb=ListRecords"

    @factory.lazy_attribute
    def request(self):
        return {
            "args": ["kenniscentra", since(self.is_initial)],
            "kwargs": {},
            "method": "get",
            "url": "https://" + self.uri,
            "headers": {},
            "data": {}
        }

    @factory.lazy_attribute
    def body(self):
        response_type = "initial" if self.is_initial else "delta"
        response_file = f"fixture.saxion.{response_type}.{self.number}.xml"
        response_file_path = os.path.join(
            settings.BASE_DIR, "sources", "factories", "fixtures",
            response_file
        )
        with open(response_file_path, "r") as response:
            return response.read()

    @classmethod
    def create_common_responses(cls, include_delta=False):
        cls.create(is_initial=True, number=0)
        cls.create(is_initial=True, number=1, resumption=RESUMPTION_TOKEN)
        if include_delta:
            cls.create(is_initial=False, number=0)
