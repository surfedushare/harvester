from django.test import TestCase, override_settings
from datagrowth.configuration import register_defaults
from datagrowth.resources.testing import ResourceFixturesMixin

from core.constants import Platforms
from core.processors import HttpSeedingProcessor
from organizations.models import Set, OrganizationDocument
from organizations.sources.sharekit import SEEDING_PHASES


class TestSharekitOrganizationSeeding(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["organizations.json"]

    @classmethod
    def setUpClass(cls):
        register_defaults("global", {
            "cache_only": True
        })
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        register_defaults("global", {
            "cache_only": False
        })
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        self.set = Set.objects.create(name="nppo", identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })

    def test_initial_seeding(self):
        for batch in self.processor("nppo", "1970-01-01T00:00:00Z"):
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
        self.assertEqual(self.set.documents.count(), 50)


@override_settings(PLATFORM=Platforms.PUBLINOVA)
class TestSharekitOrganizationExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["organizations.json"]
    seeds = []

    @classmethod
    def setUpClass(cls):
        register_defaults("global", {
            "cache_only": True
        })
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        register_defaults("global", {
            "cache_only": False
        })
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.set = Set.objects.create(name="nppo", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("nppo", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

    def test_get_state(self):
        self.assertEqual(self.seeds[0]["state"], "active")
        self.assertEqual(self.seeds[1]["state"], "deleted", "Expected inactive organizations to be deleted.")

    def test_get_set(self):
        self.assertEqual(self.seeds[0]["set"], "sharekit:nppo")

    def test_get_external_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "1182b099-53c5-465a-9505-c852d31b1a6e")

    def test_get_parents(self):
        self.assertEqual(self.seeds[0]["parents"], [])
        self.assertEqual(self.seeds[32]["parents"], [
            {"srn": "sharekit:nppo:d87a5c92-550a-4a18-bb01-1938d959a4b7", "name": "Avans Hogeschool"}
        ])

    def test_get_type(self):
        self.assertEqual(self.seeds[0]["type"], "organisation")
        self.assertEqual(self.seeds[32]["type"], "department")

    def test_get_secretary(self):
        self.assertIsNone(self.seeds[0]["secretary"])
        self.assertEqual(self.seeds[2]["secretary"],  {
            "srn": "sharekit:nppo:8200fbf4-3a09-4f28-a37f-2d8eeb08d07c",
            "name": "Hogeschool van Arnhem en Nijmegen",
            "ror": None,
            "is_root": None
        })

    def test_members(self):
        self.assertEqual(self.seeds[0]["members"], [])
        self.assertEqual(self.seeds[2]["members"], [
            {"srn": "sharekit:nppo:2ca20b3f-dad2-439c-9121-248cc336fe08", "name": "NHL Stenden Hogeschool"},
            {"srn": "sharekit:nppo:9bc007df-82c3-4bcb-9b94-1dfd5d77f9ca", "name": "Hogeschool Utrecht"},
            {"srn": "sharekit:nppo:1182b099-53c5-465a-9505-c852d31b1a6e", "name": "Zuyd Hogeschool"}
        ])
