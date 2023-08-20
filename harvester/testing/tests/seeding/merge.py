from datetime import datetime


from django.utils.timezone import make_aware

from core.processors import HttpSeedingProcessor
from testing.tests.seeding.base import HttpSeedingProcessorTestCase
from testing.models import MockHarvestResource, MockDetailResource
from testing.sources.merge import SEEDING_PHASES


class TestMergeHttpSeedingProcessor(HttpSeedingProcessorTestCase):

    def test_seeding(self):
        processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })
        results = processor("merge", "1970-01-01T00:00:00Z")

        self.assert_results(results)
        self.assert_documents()

        # Assert list resource
        self.assertEqual(
            MockHarvestResource.objects.all().count(), 1,
            "Expected one requests to list mock data endpoints"
        )
        list_resource = MockHarvestResource.objects.first()
        self.assertTrue(list_resource.success)
        self.assertEqual(list_resource.request["args"], ["merge", "1970-01-01T00:00:00Z"])
        self.assertEqual(list_resource.since, make_aware(datetime(year=1970, month=1, day=1)))
        # Assert detail resources
        self.assertEqual(
            MockDetailResource.objects.all().count(), 20,
            "Expected one request to detail mock data endpoints for each element in list data response"
        )
        for ix, resource in enumerate(MockDetailResource.objects.all()):
            self.assertTrue(resource.success)
            self.assertEqual(resource.request["args"], ["merge", ix])
