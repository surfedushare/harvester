from pathlib import Path

from django.conf import settings
from django.test import TestCase

from datagrowth.resources.testing import ResourceFixturesMixin

from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from testing.cases import seeding
from persons.models import Set, HanzePersonResource, HanzeUserResource
from persons.sources.hanze import SEEDING_PHASES


class TestHanzePersonSeeding(seeding.ResourceFixturesSeedingTestCase):

    fixtures_directory = Path(settings.BASE_DIR, "persons", "fixtures", "resources", "hanze")
    resource_fixtures = ["hanze-persons.json"]
    delta_fixtures = {
        (HanzePersonResource, 1): ("body", "hanze-persons.02.json"),
        (HanzeUserResource, 1): ("body", "hanze-user.3ce301c6-8fee-40cd-9ecd-4e6013b1d8b7.02.json"),
    }

    entity = "persons"
    source = "hanze"
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 4)
        self.assertEqual(self.set.documents.count(), 4)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "hanze:person:20bdf4bd-5aa1-4727-8795-ecc239992d2d"
        ])
        self.assertEqual(len(documents), 4, "Expected test to work with 4 documents from the delta")
        self.assertEqual(
            self.set.documents.all().count(), 4 + 1,
            "Expected 4 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 4,
            "Expected 4 Documents to have no deleted_at date and 1 with deleted_at"
        )
        new_name = "Leia Luchtloper"
        self.assertEqual(
            self.set.documents.filter(properties__author__name=new_name).count(), 1,
            "Expected name to get updated during delta harvest"
        )
        new_email = "obi-wan@theempire.spc"
        self.assertEqual(
            self.set.documents.filter(properties__sensitive__email=new_email).count(), 1,
            "Expected email to get updated during delta harvest"
        )


class TestHanzePersonExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["hanze-persons.json"]
    seeds = []

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.set = Set.objects.create(name="hanze", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("hanze", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

    def test_get_srn(self):
        self.assertEqual(self.seeds[0]["srn"], "hanze:person:3fb481c3-6db8-44b2-8a51-39e6935e9e94")

    def test_get_name(self):
        self.assertEqual(self.seeds[0]["author"]["name"], "Obi-Wan Kenobi")

    def test_get_email(self):
        self.assertEqual(self.seeds[0]["sensitive"]["email"], "obi-wan@therepublic.spc")

    def test_get_description(self):
        self.assertEqual(
            self.seeds[0]["sensitive"]["description"], "Personal profile",
            "Plain strings should be the description"
        )
        self.assertTrue(
            self.seeds[1]["sensitive"]["description"].endswith("\nMaster of Science"),
            "Expected academic qualifications to be added at end of description as list with single newlines"
        )
        self.assertIsNone(
            self.seeds[2]["sensitive"]["description"], "Expected None if there is no description data"
        )
        self.assertIn(
            "innovative music practices\n\n", self.seeds[3]["sensitive"]["description"],
            "Expected multiple sections to be joined by two newlines"
        )
        self.assertEqual(
            len(self.seeds[3]["sensitive"]["description"]), 10075,
            "Expected description concatenations to be long potentially"
        )
        expected_description_fragments = [
            "Musicians' biographical learning processes, lifelong and lifewide learning",
            "Biographical research into professional musicians, ethnographic research into innovative music practices"
        ]
        for description_fragment in expected_description_fragments:
            self.assertIn(
                description_fragment, self.seeds[3]["sensitive"]["description"],
                "Expected descriptions with the same type to be joined together in final descrption"
            )

    def test_get_isni(self):
        self.assertIsNone(
            self.seeds[0]["author"]["isni"],
            "Isni data is not available in the data."
        )

    def test_get_is_employed(self):
        self.assertTrue(self.seeds[0]["is_employed"])
        self.assertFalse(self.seeds[1]["is_employed"])
        self.assertTrue(self.seeds[2]["is_employed"])

    def test_get_job_title(self):
        self.assertEqual(self.seeds[0]["job_title"], "PhD Candidate")
        self.assertIsNone(
            self.seeds[1]["job_title"],
            "Missing job titles in staffOrganizationAssociation objects should return None"
        )

    def test_get_photo_url(self):
        self.assertEqual(self.seeds[0]["sensitive"]["photo_url"], None)
        self.assertEqual(
            self.seeds[1]["sensitive"]["photo_url"], "https://testurl/api/.jpeg",
            "Expected external links to be passed through unparsed"
        )
        self.assertEqual(
            self.seeds[2]["sensitive"]["photo_url"],
            "https://research-test.hanze.nl/ws/api/persons/4e1c0598-5e3b-43a2-abdb-6c78f726dbb5/files/ZDA4Yzg0/leia.jpg"
        )

    def test_get_skill(self):
        self.assertEqual(self.seeds[0]["skills"], [])
        self.assertEqual(self.seeds[1]["skills"], [
            "intercultural communication",
            "Intercultural Competence Development"
        ])

    def test_phone(self):
        self.assertIsNone(self.seeds[0]["sensitive"]["phone"])
        self.assertEqual(self.seeds[2]["sensitive"]["phone"], "+312012345678")
