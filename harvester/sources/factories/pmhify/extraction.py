import os
import factory

from django.conf import settings

from sources.models import PmhifyOAIPMHResource


class PmhifyOAIPMHResourceFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = PmhifyOAIPMHResource
        strategy = factory.BUILD_STRATEGY

    class Params:
        is_initial = True
        number = 0
        resumption = None
        set = "mediasite"

    status = 200
    head = {
        "content-type": "text/xml"
    }

    @factory.lazy_attribute
    def uri(self) -> str:
        return f"dev.pmhify.edusources.nl/endpoint/{self.set}/oai-pmh/?metadataPrefix=nl_LOM&verb=ListRecords"

    @factory.lazy_attribute
    def request(self) -> dict[str, None | str | list[str] | dict[str, str]]:
        return {
            "args": ["mediasite"],
            "kwargs": {},
            "method": "get",
            "url": "https://" + self.uri,
            "data": None,
            "headers": {"Content-Type": "text/xml"},
        }

    @factory.lazy_attribute
    def body(self):
        response_type = "initial" if self.is_initial else "delta"
        response_file = f"fixture.pmhify-{self.set}.{response_type}.{self.number}.xml"
        response_file_path = os.path.join(settings.BASE_DIR, "sources", "factories", "fixtures", response_file)
        with open(response_file_path, "r") as response:
            return response.read()

    @classmethod
    def create_common_responses(cls, include_delta=False):
        cls.create(is_initial=True, number=0, set="mediasite")
