import os
import factory
from datetime import datetime
from urllib.parse import quote

from django.conf import settings
from django.utils.timezone import make_aware

from sharekit.models import SharekitMetadataHarvest


class SharekitMetadataHarvestFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = SharekitMetadataHarvest
        strategy = factory.BUILD_STRATEGY

    class Params:
        set = "edusources"
        is_initial = True
        is_empty = False
        number = 0

    since = factory.Maybe(
        "is_initial",
        make_aware(datetime(year=1970, month=1, day=1)),
        make_aware(datetime(year=2020, month=2, day=10, hour=13, minute=8, second=39, microsecond=315000))
    )
    set_specification = "edusources"
    status = 200
    head = {
        "content-type": "application/json"
    }

    @factory.lazy_attribute
    def uri(self):
        base = f"api.acc.surfsharekit.nl/api/jsonapi/channel/v1/{self.set_specification}/repoItems?"
        modified_parameter = quote(f"filter[modified][GE]={self.since:%Y-%m-%dT%H:%M:%SZ}", safe="=")
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
            "args": [self.set_specification, f"{self.since:%Y-%m-%dT%H:%M:%SZ}"],
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
