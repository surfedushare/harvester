from pathlib import Path

from django.conf import settings
from django.test import TestCase

from datagrowth.resources.testing import ResourceFixturesMixin

from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from testing.cases import seeding
from projects.models import Set, BuasPureProjectResource
from projects.sources.buas import SEEDING_PHASES


class TestBuasProjectSeeding(seeding.ResourceFixturesSeedingTestCase):

    fixtures_directory = Path(settings.BASE_DIR, "projects", "fixtures", "resources", "buas")
    resource_fixtures = ["buas-test"]
    delta_fixtures = {
        (BuasPureProjectResource, 1): ("body", "buas-projects.02.pii.json")
    }

    entity = "projects"
    source = "buas"
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 100)
        self.assertEqual(self.set.documents.count(), 100)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "buas:buas:ffffffff-e6d6-4af7-8bd0-cce85d57764e"
        ])
        self.assertEqual(len(documents), 2, "Expected test to work with a small sample for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 100 + 1,
            "Expected 100 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 2,
            "Expected 2 Documents to have no deleted_at date and 97 with deleted_at, "
            "because most data didn't come in through the delta"
        )
        new_title = "K3K Consortium development zero-emissions tourism mobility"
        self.assertEqual(
            self.set.documents.filter(properties__title=new_title).count(), 1,
            "Expected title to get updated during delta harvest"
        )


class TestBUASProjectsExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["buas-test.json"]
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

    def test_get_external_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "133ce0c9-9dd6-44b8-b798-3b524f17bce0")

    def test_get_project_status(self):
        self.assertEqual(self.seeds[0]["project_status"], "finished")
        self.assertEqual(self.seeds[1]["project_status"], "to be started")
        self.assertEqual(self.seeds[31]["project_status"], "ongoing")

    def test_get_keywords(self):
        self.assertEqual(self.seeds[0]["keywords"], [
            "Zero-emissions",
            "tourism",
            "mobility",
            "transport",
            "sustainable tourism",
            "CSTT",
            "Centre for Sustainability, Tourism and Transport"
        ])
        self.assertEqual(self.seeds[46]["keywords"], [], "Expected project without keywords to return a list")

    def test_get_persons(self):
        self.assertEqual(self.seeds[0]["persons"], [
            {"external_id": "4f3e10ea-c09b-4f9e-98bb-7407d1340112", "email": None, "name": "Ikke Vogelaar"},
            {"external_id": "97ee5bd3-2145-4a4a-9a61-827e2ec839ef", "email": None, "name": "Pietje Peter"},
            {"name": "Kat Pax", "email": None, "external_id": "buas:person:b7431e1498e44deb3fb129369b08d416e23f7c3b"},
        ])

    def test_get_products(self):
        self.assertEqual(
            self.seeds[0]["products"],
            ["e3a6cbe7-1606-433d-8bca-7d42e08305c2", "e4f96a7c-029b-42b3-8039-c184e31c76d0"]
        )

    def test_get_contacts(self):
        self.assertEqual(self.seeds[0]["research_project"]["contacts"], [
            {
                "external_id": "4f3e10ea-c09b-4f9e-98bb-7407d1340112",
                "email": None,
                "name": "Ikke Vogelaar"
            }
        ])

    def test_get_owners(self):
        self.assertEqual(self.seeds[0]["research_project"]["owners"], [
            {
                "external_id": "4f3e10ea-c09b-4f9e-98bb-7407d1340112",
                "email": None,
                "name": "Ikke Vogelaar"
            }
        ])

    def test_get_parties(self):
        self.assertEqual(
            self.seeds[0]["research_project"]["parties"],
            [
                "Camptoo",
                "DEOdrive",
                "Dutch Innovation Centre for Electric Road Transport (Dutch-INCERT)",
                "Emodz",
                "EMOSS",
                "EVConsult",
                "Hansa Green Tour",
                "Rijksdienst voor Ondernemend Nederland (RVO.nl)",
            ]
        )
