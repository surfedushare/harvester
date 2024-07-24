from datetime import datetime
from urllib.parse import unquote
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils.timezone import make_aware
from django.core.exceptions import ValidationError

from sources.models.sharekit import SharekitMetadataHarvest
from sources.factories.sharekit.extraction import SharekitMetadataHarvestFactory


@override_settings(PROJECT="edusources")
class TestSharekitMetadataHarvest(TestCase):

    @classmethod
    def setUp(cls):
        cls.instance = SharekitMetadataHarvest()
        cls.base_url = "api.acc.surfsharekit.nl/api/jsonapi/channel/v1/edusources/repoItems?"

    @patch("sources.models.sharekit.SharekitMetadataHarvest.handle_errors")
    @patch("sources.models.sharekit.SharekitMetadataHarvest._send")
    def test_get_since_time(self, send_mock, handle_errors_mock):
        self.instance.get("edusources", "2021-01-01T01:00:00Z")
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(handle_errors_mock.call_count, 1)
        self.assertEqual(
            unquote(self.instance.uri),
            self.base_url + "filter[modified][GE]=2021-01-01T01:00:00Z&page[size]=25"
        )
        self.assertEqual(self.instance.since, make_aware(datetime(year=2021, month=1, day=1, hour=1)))
        self.assertEqual(self.instance.set_specification, "edusources")

    @patch("sources.models.sharekit.SharekitMetadataHarvest.handle_errors")
    @patch("sources.models.sharekit.SharekitMetadataHarvest._send")
    def test_get_since_date(self, send_mock, handle_errors_mock):
        self.instance.get("edusources", "2021-01-01")
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(handle_errors_mock.call_count, 1)
        self.assertEqual(
            unquote(self.instance.uri),
            self.base_url + "filter[modified][GE]=2021-01-01&page[size]=25"
        )
        self.assertEqual(self.instance.since, make_aware(datetime(year=2021, month=1, day=1)))
        self.assertEqual(self.instance.set_specification, "edusources")

    def test_invalid_input(self):
        try:
            self.instance.get()
            self.fail("SharekitMetadataHarvest did not raise when getting no input")
        except ValidationError:
            pass
        try:
            self.instance.get("edusources", "not-a-time-at-all!")
            self.fail("SharekitMetadataHarvest did not raise when getting invalid datetime")
        except ValidationError:
            pass

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
