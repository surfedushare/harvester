from django.test import TestCase
from datagrowth.resources.testing import ResourceFixturesMixin

from core.processors import HttpSeedingProcessor
from organizations.models import Set, OrganizationDocument
from organizations.sources.hanze import SEEDING_PHASES


class TestHanzeOrganizationSeeding(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["organizations.json"]

    def setUp(self) -> None:
        super().setUp()
        self.set = Set.objects.create(name="hanze", identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })

    def test_initial_seeding(self):
        for batch in self.processor("hanze", "1970-01-01T00:00:00Z"):
            self.assertIsInstance(batch, list)
            for product in batch:
                self.assertIsInstance(product, OrganizationDocument)
                self.assertIsNotNone(product.identity)
                self.assertTrue(product.properties)
                if product.state == OrganizationDocument.States.ACTIVE:
                    self.assertTrue(product.pending_at)
                    self.assertIsNone(product.finished_at)
                else:
                    self.assertIsNone(product.pending_at)
                    self.assertIsNotNone(product.finished_at)
        self.assertEqual(self.set.documents.count(), 20)


class TestSharekitOrganizationExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["organizations.json"]
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

    def test_get_external_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "def39560-fee1-4032-8ffc-ffccc52b058a")

    def test_get_provider(self):
        self.assertEqual(self.seeds[0]["provider"], {
            "ror": None,
            "external_id": None,
            "slug": "hanze",
            "name": "Hanze"
        })

    def test_get_name(self):
        self.assertEqual(self.seeds[0]["name"], "Hanze")

    def test_get_description(self):
        self.assertTrue(self.seeds[0]["description"].startswith("<p>Samen met studenten, professionals,"))
        self.assertIsNone(self.seeds[1]["description"], "Expected None when no description value is present")
        self.assertIsNone(self.seeds[2]["description"], "Expected None when no profile information is present")

    def test_get_ror(self):
        self.assertEqual(self.seeds[0]["ror"], "00xqtxw43")
        self.assertIsNone(self.seeds[1]["ror"], "Expected None when no ROR is present")
        self.assertIsNone(self.seeds[2]["ror"], "Expected None when no identifiers are present at all")

    def test_get_type(self):
        self.assertEqual(self.seeds[0]["type"], "university")
        self.assertEqual(self.seeds[1]["type"], "professorship")

    def test_get_parents(self):
        self.assertEqual(self.seeds[0]["parents"], [])
        self.assertEqual(self.seeds[1]["parents"], [
            {
                "srn": "hanze:organization:f372ce07-510d-47d3-9292-4322e7ebc146",
                "name": None
            }
        ])
