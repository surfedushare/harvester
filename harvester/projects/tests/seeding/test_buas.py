from django.test import TestCase

from datagrowth.resources.testing import ResourceFixturesMixin

from core.processors import HttpSeedingProcessor
from projects.models import Set
from projects.sources.buas import SEEDING_PHASES


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
