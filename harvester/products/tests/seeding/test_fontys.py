from django.test import TestCase

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from products.models import Set
from products.sources.fontys import SEEDING_PHASES, FontysProductExtractor
from sources.factories.fontys.extraction import FontysPureResourceFactory


class TestFontysProductExtraction(TestCase):

    set = None
    seeds = []

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })

        FontysPureResourceFactory.create_common_responses()

        cls.set = Set.objects.create(name="fontys:fontys", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("fontys", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

        register_defaults("global", {
            "cache_only": False
        })

    def test_get_external_id(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["external_id"], "158be0c8-1ba9-4524-9da6-ba5ff9ee03e7")

    def test_get_modified_at(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["modified_at"], "2025-06-16T10:40:02.095+02:00")

    def test_get_title(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]["title"],
            "The implementation of purpose and business ethics in terms of knowledge management"
        )

    def test_get_language(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["language"], "en")
        # Test a Dutch language product if available
        dutch_seeds = [s for s in seeds if s.get("language") == "nl"]
        if dutch_seeds:
            self.assertEqual(dutch_seeds[0]["language"], "nl")

    def test_get_publisher_year(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_year"], 2024)

    def test_get_publisher_date(self):
        seeds = self.seeds
        # Publisher date is only year for this record
        self.assertEqual(seeds[0]["publisher_year"], 2024)

    def test_get_doi(self):
        seeds = self.seeds
        # First seed may not have DOI, find one that does
        seeds_with_doi = [s for s in seeds if s.get("doi")]
        if seeds_with_doi:
            self.assertTrue(seeds_with_doi[0]["doi"].startswith("10."))

    def test_get_authors(self):
        seeds = self.seeds
        self.assertIsInstance(seeds[0]["authors"], list)
        if seeds[0]["authors"]:
            author = seeds[0]["authors"][0]
            self.assertIn("name", author)
            self.assertIn("external_id", author)
            self.assertIn("is_external", author)

    def test_get_provider(self):
        seeds = self.seeds
        provider = seeds[0]["provider"]
        self.assertEqual(provider["name"], "Fontys Hogescholen")
        self.assertEqual(provider["slug"], "fontys")

    def test_get_organizations(self):
        seeds = self.seeds
        orgs = seeds[0]["organizations"]
        self.assertIn("root", orgs)
        self.assertEqual(orgs["root"]["slug"], "fontys")

    def test_get_set(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["set"], "fontys:fontys")

    def test_get_files(self):
        # Find a seed with files
        seeds_with_files = [s for s in self.seeds if s.get("files")]
        if seeds_with_files:
            files = seeds_with_files[0]["files"]
            self.assertIsInstance(files, list)
            self.assertTrue(len(files) > 0)
            # Check that file URLs are properly formatted
            for file_url in files:
                self.assertTrue(file_url.startswith("http"))

    def test_get_keywords(self):
        seeds = self.seeds
        keywords = seeds[0].get("keywords", [])
        self.assertIsInstance(keywords, list)

    def test_get_description(self):
        # Find seeds with descriptions
        seeds_with_desc = [s for s in self.seeds if s.get("description")]
        if seeds_with_desc:
            self.assertIsInstance(seeds_with_desc[0]["description"], str)
            self.assertTrue(len(seeds_with_desc[0]["description"]) > 0)
