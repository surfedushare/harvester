from pathlib import Path

from django.conf import settings
from django.test import TestCase

from datagrowth.resources.testing import ResourceFixturesMixin

from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from testing.cases import seeding
from organizations.models import Set, PublinovaOrganizationResource
from organizations.sources.publinova import SEEDING_PHASES


class TestPublinovaOrganizationSeeding(seeding.ResourceFixturesSeedingTestCase):

    fixtures_directory = Path(settings.BASE_DIR, "organizations", "fixtures", "resources")
    resource_fixtures = ["organizations"]
    delta_fixtures = {
        (PublinovaOrganizationResource, 1): ("body", "publinova.delta.0.json")
    }

    entity = "organizations"
    source = "publinova"
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 12)
        self.assertEqual(self.set.documents.count(), 12)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "publinova:organization:d58cba84-bed2-461d-b340-4bc5492cb46a"
        ])
        self.assertEqual(len(documents), 3, "Expected limited data in delta for testing purposes.")
        self.assertEqual(
            self.set.documents.all().count(), 12 + 1,
            "Expected 12 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 3,
            "Expected 3 Documents to have no deleted_at date and 10 with deleted_at"
        )
        new_name = "Test voor Sanne **NIEUW!**"
        self.assertEqual(
            self.set.documents.filter(properties__name=new_name).count(), 1,
            "Expected name to get updated during delta harvest"
        )


class TestPublinovaOrganizationExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["organizations"]
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

    def test_get_type(self):
        self.assertEqual(self.seeds[0]["type"], "consortium")
        self.assertEqual(self.seeds[1]["type"], "professorship")
