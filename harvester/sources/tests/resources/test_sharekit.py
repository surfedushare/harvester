from urllib.parse import unquote

from django.test import TestCase, override_settings

from sources.models.sharekit import SharekitMetadataHarvest
from sources.factories.sharekit.extraction import SharekitMetadataHarvestFactory


@override_settings(PROJECT="edusources")
class TestSharekitMetadataHarvest(TestCase):

    @classmethod
    def setUp(cls):
        cls.instance = SharekitMetadataHarvest()
        cls.base_url = "api.acc.surfsharekit.nl/api/jsonapi/channel/v1/edusources/repoItems?"

    def test_create_next_request(self):
        previous = SharekitMetadataHarvestFactory()
        next_request = previous.create_next_request()
        self.assertEqual(
            unquote(next_request["url"]),
            f"https://{self.base_url}filter[modified][GE]=1970-01-01T00:00:00Z&page[size]=25&page[number]=2"
        )

    def test_handle_no_content(self):
        empty = SharekitMetadataHarvestFactory(is_empty=True)
        empty.handle_errors()
        self.assertEqual(empty.status, 204)
