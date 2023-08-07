from django.test import TestCase
from sources.factories.saxion.extraction import SaxionOAIPMHResourceFactory, RESUMPTION_TOKEN


class TestSaxionResource(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.instance = SaxionOAIPMHResourceFactory.create(is_initial=True, number=0)

    def test_next_request_parameters(self):
        # Check next parameters in isolation
        parameters = self.instance.next_parameters()
        self.assertEqual(parameters, {
            "resumptionToken": RESUMPTION_TOKEN
        })
        # Check all parameters in request URL
        request = self.instance.create_next_request()
        self.assertIn(f"resumptionToken={RESUMPTION_TOKEN}", request["url"])
        self.assertIn("verb=ListRecords", request["url"])
        self.assertIn("metadataPrefix=oai_mods", request["url"])

    def test_next_request_none(self):
        instance = SaxionOAIPMHResourceFactory.create(is_initial=True, number=1)
        parameters = instance.next_parameters()
        self.assertEqual(parameters, {})
        self.assertIsNone(instance.create_next_request())
