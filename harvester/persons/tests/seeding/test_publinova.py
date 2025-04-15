from pathlib import Path

from django.conf import settings
from django.test import TestCase

from datagrowth.resources.testing import ResourceFixturesMixin

from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from testing.cases import seeding
from persons.models import Set, PublinovaPersonResource
from persons.sources.publinova import SEEDING_PHASES


class TestHKUPersonSeeding(seeding.ResourceFixturesSeedingTestCase):

    fixtures_directory = Path(settings.BASE_DIR, "persons", "fixtures", "resources", "publinova")
    resource_fixtures = ["publinova-persons.json"]
    delta_fixtures = {
        (PublinovaPersonResource, 1): ("body", "publinova-persons.01b.pii.json")
    }

    entity = "persons"
    source = "publinova"
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 50)
        self.assertEqual(self.set.documents.count(), 50)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "publinova:person:11101732-cd9b-490f-a51a-625fcc908995"
        ])
        self.assertEqual(len(documents), 25, "Expected test to work with a small sample for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 50 + 1,
            "Expected 50 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 25,
            "Expected 26 Documents to have no deleted_at date and 25 with deleted_at, "
            "because most data didn't come in through the delta"
        )
        new_name = "Luitje"
        self.assertEqual(
            self.set.documents.filter(properties__author__name=new_name).count(), 1,
            "Expected name to get updated during delta harvest"
        )


class TestPublinovaPersonExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["publinova-persons.json"]
    seeds = []

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.set = Set.objects.create(name="publinova", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("publinova", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

    def test_get_srn(self):
        self.assertEqual(self.seeds[0]["srn"], "publinova:person:00001732-cd9b-490f-a51a-625fcc908884")

    def test_get_name(self):
        self.assertEqual(self.seeds[0]["author"]["name"], "Mystery Girl")
        self.assertEqual(self.seeds[1]["author"]["name"], "Luís in je Pels")

    def test_get_description(self):
        self.assertEqual(self.seeds[0]["sensitive"]["description"], "Who is about to disappear")
