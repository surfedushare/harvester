from unittest.mock import patch
from datetime import datetime

from django.utils.timezone import make_aware

from core.processors import HttpSeedingProcessor
from testing.tests.seeding.base import HttpSeedingProcessorTestCase
from testing.models import MockHarvestResource
from testing.sources.nested import SEEDING_PHASES


NESTING_PARAMETERS = {
    "size": 20,
    "page_size": 10,
    "nested": "simple"
}


class TestNestedHttpSeedingProcessor(HttpSeedingProcessorTestCase):

    @patch.object(MockHarvestResource, "PARAMETERS", NESTING_PARAMETERS)
    def test_seeding(self):
        processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })
        results = processor("nested", "1970-01-01T00:00:00Z")

        self.assert_results(results, extra_keys=["parent_id"])  # extraction method adds this key to defaults
        self.assert_documents(expected_documents=19)  # due to the way generated nested seeds get divided we loose one

        # Assert resources
        self.assertEqual(MockHarvestResource.objects.all().count(), 2, "Expected two requests to mock data endpoints")
        for resource in MockHarvestResource.objects.all():
            self.assertTrue(resource.success)
            self.assertEqual(resource.request["args"], ["nested", "1970-01-01T00:00:00Z"])
            self.assertEqual(resource.since, make_aware(datetime(year=1970, month=1, day=1)))
