from pathlib import Path

from django.conf import settings
from django.test import TestCase

from datagrowth.resources.testing import ResourceFixturesMixin

from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from testing.cases import seeding
from persons.models import Set, BuasPersonResource
from persons.sources.buas import SEEDING_PHASES


class TestBuasPersonSeeding(seeding.ResourceFixturesSeedingTestCase):

    fixtures_directory = Path(settings.BASE_DIR, "persons", "fixtures", "resources", "buas")
    resource_fixtures = ["buas-persons.json"]
    delta_fixtures = {
        (BuasPersonResource, 1): ("body", "buas-persons.02.json"),
    }

    entity = "persons"
    source = "buas"
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 3)
        self.assertEqual(self.set.documents.count(), 3)

    def test_delta_seeding(self, *args) -> None:
        documents = super().test_delta_seeding([
            "buas:person:fcfba7fc-eebf-409d-9359-1d4efeb7ac78"
        ])
        self.assertEqual(len(documents), 3, "Expected test to work with 3 documents from the delta")
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
            "Expected 3 Documents to have no deleted_at date and 1 with deleted_at"
        )
        new_description = "<p><strong>Ozzie Bassie</strong></p>"
        self.assertEqual(
            self.set.documents.filter(properties__sensitive__description=new_description).count(), 1,
            "Expected description to get updated during delta harvest"
        )


class TestBUASPersonsExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["buas-persons.json"]
    seeds = []

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.set = Set.objects.create(name="buas", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("buas", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

    def test_get_name(self):
        self.assertEqual(self.seeds[0]["author"]["name"], "F Maggie")

    def test_get_description(self):
        self.assertIsNone(self.seeds[0]["sensitive"]["description"])
        self.assertTrue(
            self.seeds[1]["sensitive"]["description"].startswith(
                "<p><strong>Ozzie Bassie</strong> (1990) is a researcher and lecturer"
            )
        )

    def test_get_skills(self):
        self.assertEqual(self.seeds[0]["skills"], [])
        self.assertEqual(self.seeds[1]["skills"], [
            "Multi-narrative design (transmedia)", "semiotics", "virtual reality"
        ])

    def test_get_email(self):
        self.assertIsNone(self.seeds[0]["sensitive"]["email"])
        self.assertEqual(self.seeds[1]["sensitive"]["email"], "bassie@buas.nl")

    def test_get_photo_url(self):
        self.assertIsNone(self.seeds[0]["sensitive"]["photo_url"])
        self.assertEqual(
            self.seeds[1]["sensitive"]["photo_url"],
            "https://pure.buas.nl/ws/files/251152/Bassie_Ozzie.jpg"
        )

    def test_get_is_employed(self):
        self.assertFalse(self.seeds[0]["is_employed"])
        self.assertTrue(self.seeds[1]["is_employed"])
        self.assertFalse(self.seeds[2]["is_employed"])

    def test_get_job_title(self):
        self.assertIsNone(self.seeds[0]["job_title"])
        self.assertEqual(self.seeds[1]["job_title"], "Lecturer")
        self.assertIsNone(self.seeds[2]["job_title"])

    def test_socials(self):
        self.assertEqual(self.seeds[0]["sensitive"]["socials"], [])
        self.assertEqual(self.seeds[1]["sensitive"]["socials"], [
            {
                "type": "linkedin",
                "url": "http://www.linkedin.com/in/ozzie-bassie",
            }
        ])