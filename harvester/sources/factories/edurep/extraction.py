import os
import factory
from datetime import datetime
from urllib.parse import quote

from django.conf import settings
from django.utils.timezone import make_aware

from sources.models import EdurepOAIPMH


def since(is_initial) -> str:
    if is_initial:
        date = make_aware(datetime(year=1970, month=1, day=1))
    else:
        date = make_aware(datetime(year=2020, month=2, day=10, hour=13, minute=8, second=39, microsecond=315000))
    return f"{date:%Y-%m-%dT%H:%M:%SZ}"


class EdurepOAIPMHFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = EdurepOAIPMH
        strategy = factory.BUILD_STRATEGY

    class Params:
        is_initial = True
        is_empty = False
        is_deletes = False
        number = 0
        resumption = None

    status = 200
    head = {
        "content-type": "text/xml"
    }

    @factory.lazy_attribute
    def uri(self):
        from_param = f"from={since(self.is_initial)}"
        identity = quote(f"{from_param}&metadataPrefix=lom&set=edurep", safe="=&") \
            if not self.resumption else f"resumptionToken={quote(self.resumption)}"
        return f"staging.edurep.kennisnet.nl/edurep/oai?{identity}&verb=ListRecords"

    @factory.lazy_attribute
    def request(self):
        return {
            "args": ["edurep", since(self.is_initial)],
            "kwargs": {},
            "method": "get",
            "url": "https://" + self.uri,
            "headers": {},
            "data": {}
        }

    @factory.lazy_attribute
    def body(self):
        if self.is_empty:
            response_sequence = self.number
            response_type = "empty"
        elif self.is_deletes:
            response_sequence = self.number
            response_type = "deletes"
        elif self.is_initial:
            response_sequence = self.number
            response_type = "initial"
        else:
            response_sequence = 0
            response_type = "delta"
        response_file = f"fixture.edurep.{response_type}.{response_sequence}.xml"
        response_file_path = os.path.join(settings.BASE_DIR, "sources", "factories", "fixtures", response_file)
        with open(response_file_path, "r") as response:
            return response.read()

    @classmethod
    def create_common_responses(cls, include_delta=False):
        cls.create(is_initial=True, number=0)
        cls.create(is_initial=True, number=1, resumption="c1576069959151499|u|f1970-01-01T00:00:00Z|mlom|ssurf")
        if include_delta:
            cls.create(is_initial=False, number=0)
