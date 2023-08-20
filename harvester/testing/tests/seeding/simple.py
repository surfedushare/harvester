from datetime import datetime

from django.utils.timezone import make_aware

from core.processors import HttpSeedingProcessor
from testing.tests.seeding.base import HttpSeedingProcessorTestCase
from testing.models import MockHarvestResource
from testing.sources.simple import SEEDING_PHASES


class TestSimpleHttpSeedingProcessor(HttpSeedingProcessorTestCase):

    def test_seeding(self):
        processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })
        results = processor("simple", "1970-01-01T00:00:00Z")

        self.assert_results(results)
        self.assert_documents()

        # Assert resources
        self.assertEqual(MockHarvestResource.objects.all().count(), 2, "Expected two requests to mock data endpoints")
        for resource in MockHarvestResource.objects.all():
            self.assertTrue(resource.success)
            self.assertEqual(resource.request["args"], ["simple", "1970-01-01T00:00:00Z"])
            self.assertEqual(resource.since, make_aware(datetime(year=1970, month=1, day=1)))
