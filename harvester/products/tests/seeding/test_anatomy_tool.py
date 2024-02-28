from datagrowth.configuration import register_defaults
from django.test import TestCase

from core.processors import HttpSeedingProcessor
from core.tests.base import SeedExtractionTestCase
from products.models import Set, ProductDocument
from products.sources.anatomy_tool import SEEDING_PHASES
from sources.factories.anatomy_tool.extraction import AnatomyToolOAIPMHFactory


class TestAnatomyToolProductSeeding(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        register_defaults("global", {
            "cache_only": True
        })

    @classmethod
    def tearDownClass(cls):
        register_defaults("global", {
            "cache_only": False
        })
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        AnatomyToolOAIPMHFactory.create_common_responses()

    def setUp(self) -> None:
        super().setUp()
        self.set = Set.objects.create(identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })

    def test_initial_seeding(self):
        for batch in self.processor("anatomy_tool", "1970-01-01T00:00:00Z"):
            self.assertIsInstance(batch, list)
            for product in batch:
                self.assertIsInstance(product, ProductDocument)
                self.assertIsNotNone(product.identity)
                self.assertTrue(product.properties)
                if product.state == ProductDocument.States.ACTIVE:
                    self.assertTrue(product.pending_at)
                    self.assertIsNone(product.finished_at)
                else:
                    self.assertIsNone(product.pending_at)
                    self.assertIsNotNone(product.finished_at)
        self.assertEqual(self.set.documents.count(), 10)


class TestAnatomyToolProductExtraction(SeedExtractionTestCase):

    set = None
    seeds = []

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })
        AnatomyToolOAIPMHFactory.create_common_responses()
        cls.set = Set.objects.create(identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("anatomy_tool", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]
        register_defaults("global", {
            "cache_only": False
        })

    def test_authors_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['authors'], [
            {'name': 'O. Paul Gobée', 'email': None, 'external_id': None, 'dai': None, 'orcid': None, 'isni': None},
            {'name': 'Prof. X. Test', 'email': None, 'external_id': None, 'dai': None, 'orcid': None, 'isni': None}
        ])

    def test_lom_educational_level(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["learning_material"]["lom_educational_levels"], ["HBO", "WO"])

    def test_get_files(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["files"], ["https://anatomytool.org/node/56055"])
        self.assertEqual(seeds[6]["files"], ["https://anatomytool.org/node/56176"])

    def test_get_copyright(self):
        seeds = self.seeds
        self.assertEqual(len(seeds), 10, "Expected get_harvest_seeds to filter differently based on copyright")
        self.assertEqual(seeds[0]["copyright"], "cc-by-nc-sa-40")
        self.assertEqual(seeds[6]["copyright"], "yes")

    def test_get_keywords(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["keywords"], ['A05.6.02.001 Duodenum', 'A05.9.01.001 Pancreas'])

    def test_get_publisher_date(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_date"], "2016-06-05")
        self.assertIsNone(seeds[1]["publisher_date"])

    def test_get_publisher_year(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_year"], 2016)
        self.assertIsNone(seeds[1]["publisher_year"])
