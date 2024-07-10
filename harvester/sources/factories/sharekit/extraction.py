import os
import factory
from datetime import datetime
from urllib.parse import quote

from django.conf import settings
from django.utils.timezone import make_aware

from sources.models.sharekit import SharekitMetadataHarvest


def since(is_initial) -> str:
    if is_initial:
        date = make_aware(datetime(year=1970, month=1, day=1))
    else:
        date = make_aware(datetime(year=2020, month=2, day=10, hour=13, minute=8, second=39, microsecond=315000))
    return f"{date:%Y-%m-%dT%H:%M:%SZ}"


class SharekitMetadataHarvestFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = SharekitMetadataHarvest
        strategy = factory.BUILD_STRATEGY

    class Params:
        set = "edusources"
        is_initial = True
        is_empty = False
        is_deletes = False
        number = 0

    status = 200
    head = {
        "content-type": "application/json"
    }

    @factory.lazy_attribute
    def uri(self):
        base = "api.acc.surfsharekit.nl/api/jsonapi/channel/v1/edusources/repoItems?"
        modified_parameter = quote(f"filter[modified][GE]={since(self.is_initial)}", safe="=")
        page_size_parameter = quote("page[size]=25", safe="=")
        page_number_parameter = quote(f"page[number]={self.number+1}", safe="=")
        if self.number > 0:
            params = [modified_parameter, page_number_parameter, page_size_parameter]
        else:
            params = [modified_parameter, page_size_parameter]
        return base + "&".join(params)

    @factory.lazy_attribute
    def request(self):
        return {
            "args": ["edusources", since(self.is_initial)],
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
        response_file = f"fixture.sharekit.{response_type}.{response_sequence}.json"
        response_file_path = os.path.join(settings.BASE_DIR, "sources", "factories", "fixtures", response_file)
        with open(response_file_path, "r") as response:
            return response.read()

    @classmethod
    def create_common_sharekit_responses(cls, include_delta=False):
        cls.create(is_initial=True, number=0)
        cls.create(is_initial=True, number=1)
        if include_delta:
            cls.create(is_initial=False, number=0)
