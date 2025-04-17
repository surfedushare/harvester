from pathlib import Path

from django.conf import settings
from django.test import TestCase

from datagrowth.resources.testing import ResourceFixturesMixin

from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from testing.cases import seeding
from projects.models import Set, PublinovaProjectsResource
from projects.sources.publinova import SEEDING_PHASES


class TestPublinovaProjectSeeding(seeding.ResourceFixturesSeedingTestCase):

    fixtures_directory = Path(settings.BASE_DIR, "projects", "fixtures", "resources", "publinova")
    resource_fixtures = ["publinova-projects"]
    delta_fixtures = {
        (PublinovaProjectsResource, 2): ("body", "publinova-projects.02b.pii.json")
    }

    entity = "projects"
    source = "publinova"
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 13)
        self.assertEqual(self.set.documents.count(), 13)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "publinova:project:c1d844d8-c267-4b06-b2aa-26a647d9849b"
        ])
        self.assertEqual(len(documents), 13, "Expected delta with delete policy 'no' to revisit all data.")
        self.assertEqual(
            self.set.documents.all().count(), 13 + 1,
            "Expected 13 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 13,
            "Expected 12 Documents to have no deleted_at date and 1 with deleted_at"
        )
        new_title = "MACHINE LEARNING!"
        self.assertEqual(
            self.set.documents.filter(properties__title=new_title).count(), 1,
            "Expected title to get updated during delta harvest"
        )


class TestPublinovaProjectsExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["publinova-projects"]
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

    def test_srn(self):
        self.assertEqual(self.seeds[0]["srn"], "publinova:project:025e429e-05e1-4e19-89fb-803c3740a88c")

    def test_get_project_status(self):
        self.assertEqual(self.seeds[0]["project_status"], "unknown")
        self.assertEqual(self.seeds[3]["project_status"], "ongoing")

    def test_get_keywords(self):
        self.assertEqual(self.seeds[0]["keywords"], [])
        self.assertEqual(self.seeds[3]["keywords"], ["energy transition"])

    def test_get_contacts(self):
        self.assertEqual(self.seeds[0]["research_project"]["contacts"], [])
        self.assertEqual(self.seeds[3]["research_project"]["contacts"], [
            {
                "external_id": "0086b08d-1776-4de8-bfa6-a3381475ce92",
                "email": None,
                "name": "Atje de Boer"
            }
        ])

    def test_get_owners(self):
        self.assertEqual(self.seeds[0]["research_project"]["owners"], [
            {
                "external_id": "3803adec-2662-4da0-ae63-19aa5bbd3bcf",
                "email": "info@anoniem.nl",
                "name": "Zooma Test 28 nov"
            }
        ])

    def test_get_parties(self):
        self.assertEqual(self.seeds[0]["research_project"]["parties"], ["Onbekend"])
        self.assertEqual(self.seeds[1]["research_project"]["parties"], ["SURF test"])

    def test_get_themes(self):
        self.assertEqual(self.seeds[0]["research_project"]["themes"], [])
        self.assertEqual(self.seeds[5]["research_project"]["themes"], ["Bouw & Logistiek"])

    def test_get_started_at(self):
        self.assertIsNone(self.seeds[0]["started_at"])
        self.assertEqual(self.seeds[3]["started_at"], "2024-05-09T00:00:00")

    def test_get_ended_at(self):
        self.assertIsNone(self.seeds[0]["ended_at"])
        self.assertEqual(self.seeds[3]["ended_at"], "2024-05-18T00:00:00")
