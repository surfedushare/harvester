import os
import factory
from datetime import datetime
from urllib.parse import quote

from django.conf import settings
from django.utils.timezone import make_aware

from sources.models import SaxionOAIPMHResource


SLUG = "saxion"
uri = SaxionOAIPMHResource.URI_TEMPLATE.replace("https://", "")
start_params = uri.find("?")
ENDPOINT = uri[:start_params]
SET_SPECIFICATION = "kenniscentra"
METADATA_PREFIX = "oai_mods"
RESUMPTION_TOKEN = "5608392947620842476"


class SaxionOAIPMHResourceFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = SaxionOAIPMHResource
        strategy = factory.BUILD_STRATEGY

    class Params:
        is_initial = True
        number = 0
        resumption = None

    since = factory.Maybe(
        "is_initial",
        make_aware(datetime(year=1970, month=1, day=1)),
        make_aware(datetime(year=2020, month=1, day=1))
    )
    set_specification = SET_SPECIFICATION
    status = 200
    head = {
        "content-type": "text/xml"
    }

    @factory.lazy_attribute
    def uri(self):
        from_param = quote(f"{self.since:%Y-%m-%dT%H:%M:%SZ}")
        identity = f"from={from_param}&metadataPrefix={METADATA_PREFIX}"
        if self.resumption:
            identity += f"&resumptionToken={quote(self.resumption)}"
        identity += f"&set={self.set_specification}"
        return f"{ENDPOINT}?{identity}&verb=ListRecords"

    @factory.lazy_attribute
    def request(self):
        return {
            "args": [self.set_specification, f"{self.since:%Y-%m-%dT%H:%M:%SZ}"],
            "kwargs": {},
            "method": "get",
            "url": "https://" + self.uri,
            "headers": {},
            "data": {}
        }

    @factory.lazy_attribute
    def body(self):
        response_type = "initial" if self.is_initial else "delta"
        response_file = f"fixture.{SLUG}.{response_type}.{self.number}.xml"
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
