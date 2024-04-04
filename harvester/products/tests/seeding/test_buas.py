from django.test import TestCase

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from products.models import Set
from products.sources.buas import SEEDING_PHASES
from sources.factories.buas.extraction import BuasPureResourceFactory


class TestBuasProductExtraction(TestCase):

    set = None
    seeds = []

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })
        BuasPureResourceFactory.create_common_responses()
        cls.set = Set.objects.create(name="buas:buas", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("buas", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]
        register_defaults("global", {
            "cache_only": False
        })

    def test_get_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "b7b17301-7123-4113-aa8a-8391aa9d7e01")

    def test_get_files(self):
        self.assertEqual(self.seeds[0]["files"], [])
        self.assertEqual(self.seeds[1]["files"], [
            "http://www.control-online.nl/gamesindustrie/2010/04/26/nieuw-column-op-maandag/",
        ])
        self.assertEqual(self.seeds[3]["files"], [
            "https://pure.buas.nl/ws/files/15672869/Peeters_tourismandclimatemitigation_peetersp_ed_nhtv2007.pdf"
        ])

    def test_get_url(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]["url"],
            "https://pure.buas.nl/en/publications/b7b17301-7123-4113-aa8a-8391aa9d7e01"
        )
        self.assertEqual(
            seeds[1]["url"],
            "http://www.control-online.nl/gamesindustrie/2010/04/26/nieuw-column-op-maandag/"
        )

    def test_get_mime_type(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]["mime_type"])
        self.assertEqual(seeds[1]["mime_type"], "text/html")

    def test_get_analysis_allowed(self):
        seeds = self.seeds
        self.assertFalse(seeds[0]["analysis_allowed"])
        self.assertTrue(seeds[1]["analysis_allowed"])

    def test_get_language(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["language"], {"metadata": "en"})
        self.assertEqual(seeds[4]["language"], {"metadata": "en"})

    def test_get_title(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["title"], "Edinburgh inspiring capital : ensuring world beats a path to our doors")

    def test_get_description(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]["description"],
            "<p>Edinburgh inspiring capital : ensuring world beats a path to our doors</p>"
        )
        self.assertIsNone(seeds[1]["description"])

    def test_get_keywords(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["keywords"], [
            "inspiring capital",
            "beat the world",
        ])
        self.assertEqual(seeds[1]["keywords"], [])

    def test_authors_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['authors'], [
            {
                'name': 'KJ Dinnie', 'email': None, 'external_id': '6f1bbf4a-b32a-4923-9f47-bb764f3dbbde',
                'dai': None, 'orcid': None, 'isni': None
            }
        ])

    def test_publisher_year(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_year"], 2012)

    def test_research_object_type(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["research_object_type"], "Article")

    def test_publisher_date(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_date"], "2012-06-07")
        self.assertEqual(seeds[9]["publisher_date"], "2010-01-14")
