import os
import factory
from datetime import datetime
from urllib.parse import quote

from django.conf import settings
from django.utils.timezone import make_aware

from sources.models import GreeniOAIPMHResource


SLUG = "greeni"
uri = GreeniOAIPMHResource.URI_TEMPLATE.replace("https://", "")
start_params = uri.find("?")
ENDPOINT = uri[:start_params]
SET_SPECIFICATION = "PUBVHL"
METADATA_PREFIX = "didl"
RESUMPTION_TOKEN = "PUBVHL|didl|1840-12-31|9999-12-31|^2^139717|66191,57659"


class GreeniOAIPMHResourceFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = GreeniOAIPMHResource
        strategy = factory.BUILD_STRATEGY

    class Params:
        is_initial = True
        number = 0
        resumption = None

    since = factory.Maybe(
        "is_initial",
        make_aware(datetime(year=1970, month=1, day=1)),
        make_aware(datetime(year=2020, month=2, day=10))
    )
    set_specification = SET_SPECIFICATION
    status = 200
    head = {
        "content-type": "text/xml"
    }

    @factory.lazy_attribute
    def uri(self):
        identity = f"from={self.since:%Y-%m-%d}&metadataPrefix={METADATA_PREFIX}&set={self.set_specification}"
        if self.resumption:
            identity = f"resumptionToken={quote(self.resumption)}"
        return f"{ENDPOINT}?{identity}&verb=ListRecords"

    @factory.lazy_attribute
    def request(self):
        return {
            "args": [self.set_specification, f"{self.since:%Y-%m-%d}"],
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
