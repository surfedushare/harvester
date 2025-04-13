from pathlib import Path

from django.conf import settings
from django.test import TestCase

from datagrowth.resources.testing import ResourceFixturesMixin

from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from testing.cases import seeding
from persons.models import Set, HkuPersonResource
from persons.sources.hku import SEEDING_PHASES


class TestHKUPersonSeeding(seeding.ResourceFixturesSeedingTestCase):

    fixtures_directory = Path(settings.BASE_DIR, "persons", "fixtures", "resources", "hku")
    resource_fixtures = ["hku-persons.json"]
    delta_fixtures = {
        (HkuPersonResource, 1): ("body", "hku-persons.02.json")
    }

    entity = "persons"
    source = "hku"
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 2)
        self.assertEqual(self.set.documents.count(), 2)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "hku:person:3"
        ])
        self.assertEqual(len(documents), 2, "Expected test to work with a small sample for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 2 + 1,
            "Expected 2 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 2,
            "Expected 2 Documents to have no deleted_at date and 1 with deleted_at, "
            "because most data didn't come in through the delta"
        )
        new_description = "<p>Pietje Puk is a super hero!</p>"
        self.assertEqual(
            self.set.documents.filter(properties__sensitive__description=new_description).count(), 1,
            "Expected description to get updated during delta harvest"
        )


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

    def test_get_name(self):
        self.assertEqual(self.seeds[0]["author"]["name"], "Pietje Puk")

    def test_get_email(self):
        self.assertEqual(self.seeds[0]["sensitive"]["email"], "pietje.puk@hku.nl")

    def test_get_description(self):
        self.assertEqual(self.seeds[0]["sensitive"]["description"], "<p>Pietje Puk is a researcher and designer</p>")

    def test_get_skills(self):
        self.assertEqual(self.seeds[0]["skills"], ["skills-yo"])

    def test_get_themes(self):
        self.assertEqual(self.seeds[0]["researcher"]["themes"], ["Taal, Cultuur en Kunsten", "Techniek"])

    def test_get_orcid(self):
        self.assertEqual(self.seeds[0]["researcher"]["orcid"], "0000-0000-0000-0001")
