from django.test import TestCase, override_settings

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from products.models import Set
from products.sources.hva import SEEDING_PHASES
from sources.factories.hva.extraction import HvaPureResourceFactory


@override_settings(SOURCES_MIDDLEWARE_API="http://testserver/api/v1/")
class TestHvaProductExtraction(TestCase):

    set = None
    seeds = []

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })

        HvaPureResourceFactory.create_common_responses()
        cls.set = Set.objects.create(name="hva", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("hva", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

        register_defaults("global", {
            "cache_only": False
        })

    def test_get_id(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["external_id"], "7288bd68-d62b-4db0-8cea-5f189e209254")

    def test_get_files(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["files"], [])
        self.assertEqual(seeds[3]["files"], [
            "http://testserver/api/v1/files/hva/d7126f6d-c412-43c8-ad2a-6acb7613917d/files/"
            "MDIyMzRi/636835_schuldenvrij-de-weg-naar-werk_aangepast.pdf",
        ])

    def test_get_language(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["language"], "nl")
        self.assertEqual(seeds[4]["language"], "en")

    def test_get_title(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["title"], "Leerlingen in het Amsterdamse onderwijs")

    def test_get_description(self):
        seeds = self.seeds
        self.assertTrue(seeds[0]["description"].startswith("De relatie tussen schoolloopbanen van jongeren"))

    def test_keywords(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["keywords"], ['onderzoek', 'leerlingen', 'Amsterdam', 'schoolloopbanen', 'jongeren'])

    def test_authors_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['authors'], [
            {
                'name': 'Ruben Fukkink', 'email': None,
                'external_id': "c16dbff7-4c77-463a-9d91-933bf59bbc53",
                'dai': None, 'orcid': None, 'isni': None
            },
            {
                'name': 'Sandra van Otterloo', 'email': None,
                'external_id': "hva:person:effd42a504e9a5d3963603848288d13af3188cc5",
                'dai': None, 'orcid': None, 'isni': None
            },
            {
                'name': 'Lotje Cohen', 'email': None,
                'external_id': "hva:person:412ed1fc512e775ddca58e0655220b44c50a8b20",
                'dai': None, 'orcid': None, 'isni': None
            },
            {
                'name': 'Merel van der Wouden', 'email': None,
                'external_id': "hva:person:e3a6d0b12c0e42a2afd2811d65f512b11f947d6f",
                'dai': None, 'orcid': None, 'isni': None
            },
            {
                'name': 'Bonne Zijlstra', 'email': None,
                'external_id': "hva:person:45fec1047bbfe2dda5d740d7c4b046e85af084ae",
                'dai': None, 'orcid': None, 'isni': None
            }
        ])

    def test_publisher_year(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_year"], 2016)

    def test_research_object_type(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["research_product"]["research_object_type"], "Report")

    def test_doi(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]["doi"])
        self.assertEqual(seeds[5]["doi"], "10.1088/0031-+9120/+50/5/573")

    def test_publisher_date(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_date"], "2016-01-01")
        self.assertEqual(seeds[1]["publisher_date"], "2016-02-01")
        self.assertIsNone(seeds[5]["publisher_date"])
