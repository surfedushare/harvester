from urllib.parse import unquote

from django.test import TestCase

from datagrowth.exceptions import DGHttpError50X, DGHttpError40X
from sources.models import EdurepOAIPMH
from sources.factories.edurep.extraction import EdurepOAIPMHFactory


class TestEdurepOAIPMH(TestCase):

    @classmethod
    def setUp(cls):
        cls.instance = EdurepOAIPMH()

    def test_create_next_request(self):
        previous = EdurepOAIPMHFactory()
        next_request = previous.create_next_request()
        self.assertEqual(
            unquote(next_request["url"]),
            "https://staging.edurep.kennisnet.nl/edurep/oai"
            "?verb=ListRecords&resumptionToken=c1576069959151499|u|f1970-01-01T00:00:00Z|mlom|ssurf"
        )

    def test_handle_errors(self):
        # We'll handle a few cases here:
        # Something very bad with no response at all
        try:
            self.instance.handle_errors()
            self.fail("Empty EdurepOAIPMH did not indicate any kind of network error")
        except DGHttpError50X:
            pass
        # Something wrong with the request
        # Note that this returns 200 and we transform this into something sensible,
        # but we simply fake such a response here
        try:
            self.instance.status = 200
            self.instance.head = {
                "content-type": "text/xml"
            }
            self.instance.body = '<error code="badArgument"></error>'
            self.instance.handle_errors()
            self.fail("EdurepOAIPMH did not raise after receiving a badArgument error")
        except DGHttpError40X:
            self.assertEqual(self.instance.status, 400)
        # Empty response
        # Note that this returns 200 and we transform this into something sensible,
        # but we simply fake such a response here
        self.instance.status = 200
        self.instance.head = {
            "content-type": "text/xml"
        }
        self.instance.body = '<error code="noRecordsMatch"></error>'
        self.instance.handle_errors()
        self.assertEqual(self.instance.status, 204,
                         "Expected EdurepOAIPMH to translate noRecordsMatch error into a no content response")
