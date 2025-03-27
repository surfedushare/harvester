from pathlib import Path

from django.conf import settings
from django.test import TestCase

from datagrowth.resources.testing import ResourceFixturesMixin

from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from testing.cases import seeding
from persons.models import Set
from persons.sources.hku import SEEDING_PHASES


class TestHKUProjectSeeding(seeding.ResourceFixturesSeedingTestCase):

    fixtures_directory = Path(settings.BASE_DIR, "persons", "fixtures", "resources", "hku")
    resource_fixtures = ["hku-persons.json"]

    entity = "persons"
    source = "hku"
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 1)
        self.assertEqual(self.set.documents.count(), 1)

    def test_delta_seeding(self, *args):
        pass


class TestHKUPersonExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["hku-persons.json"]
    seeds = []

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.set = Set.objects.create(name="hku", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("hku", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

    def test_get_srn(self):
        self.assertEqual(self.seeds[0]["srn"], "hku:person:1")

    def test_get_external_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "1")

    def test_get_prefix(self):
        self.assertIsNone(self.seeds[0]["author"]["prefix"])
