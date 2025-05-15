from pathlib import Path

from django.conf import settings
from django.test import TestCase

from datagrowth.resources.testing import ResourceFixturesMixin

from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from testing.cases import seeding
from persons.models import Set, HuPersonResource
from persons.sources.hu import SEEDING_PHASES


class TestHUPersonSeeding(seeding.ResourceFixturesSeedingTestCase):

    fixtures_directory = Path(settings.BASE_DIR, "persons", "fixtures", "resources", "hu")
    resource_fixtures = ["hu-persons.json"]
    delta_fixtures = {
        (HuPersonResource, 1): ("body", "hu-persons.02.json")
    }

    entity = "persons"
    source = "hu"
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 3)
        self.assertEqual(self.set.documents.count(), 3)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "hu:person:c2f5b225-e8e7-4b20-9db6-750321e650ab"
        ])
        self.assertEqual(len(documents), 3, "Expected test to work with a small sample for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 3 + 1,
            "Expected 3 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 3,
            "Expected 3 Documents to have no deleted_at date and 1 with deleted_at, "
            "because most data didn't come in through the delta"
        )
        new_description = "<p>Hij is een aap</p>"
        self.assertEqual(
            self.set.documents.filter(properties__sensitive__description=new_description).count(), 1,
            "Expected description to get updated during delta harvest"
        )


class TestHUPersonExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["hu-persons.json"]
    seeds = []

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.set = Set.objects.create(name="hu", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("hu", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

    def test_get_srn(self):
        self.assertEqual(self.seeds[0]["srn"], "hu:person:4bc16849-1e9a-4b37-8c66-860ce2f01c69")
