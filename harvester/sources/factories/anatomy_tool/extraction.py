import os
import factory
from datetime import datetime
from urllib.parse import quote

from django.conf import settings
from django.utils.timezone import make_aware

from sources.models import AnatomyToolOAIPMH


def since(is_initial) -> str:
    if is_initial:
        date = make_aware(datetime(year=1970, month=1, day=1))
    else:
        date = make_aware(datetime(year=2020, month=1, day=1))
    return f"{date:%Y-%m-%dT%H:%M:%SZ}"


class AnatomyToolOAIPMHFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = AnatomyToolOAIPMH
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
    def uri(self) -> str:
        from_param = f"from={since(self.is_initial)}"
        identity = quote(f"{from_param}&metadataPrefix=nl_lom", safe="=&") \
            if not self.resumption else f"resumptionToken={quote(self.resumption)}"
        return f"anatomytool.org/oai-pmh?{identity}&verb=ListRecords"

    @factory.lazy_attribute
    def request(self) -> dict[str, None | str | list[str] | dict[str, str]]:
        return {
            "args": ["anatomy_tool", since(self.is_initial)],
            "kwargs": {},
            "method": "get",
            "url": "https://" + self.uri,
            "data": None,
            "headers": {"Content-Type": "text/xml"},
        }

    @factory.lazy_attribute
    def body(self):
        response_type = "initial" if self.is_initial else "delta"
        response_file = f"fixture.anatomy_tool.{response_type}.{self.number}.xml"
        response_file_path = os.path.join(settings.BASE_DIR, "sources", "factories", "fixtures", response_file)
        with open(response_file_path, "r") as response:
            return response.read()

    @classmethod
    def create_common_responses(cls, include_delta=False):
        cls.create(is_initial=True, number=0)
        cls.create(is_initial=True, number=1, resumption="6dc475814880745c5c55bba3fb288c35")

    @classmethod
    def create_delta_responses(cls):
        cls.create(is_initial=False, number=0)
