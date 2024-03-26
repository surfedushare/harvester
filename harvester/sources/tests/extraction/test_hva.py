from datetime import datetime

from django.test import TestCase, override_settings
from django.utils.timezone import make_aware

from harvester.utils.extraction import get_harvest_seeds
from core.constants import Repositories
from sources.factories.hva.extraction import HvaPureResourceFactory, SET_SPECIFICATION


@override_settings(SOURCES_MIDDLEWARE_API="http://testserver/api/v1/")
class TestGetHarvestSeedsHva(TestCase):

    begin_of_time = None
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.begin_of_time = make_aware(datetime(year=1970, month=1, day=1))
        HvaPureResourceFactory.create_common_responses()
        cls.seeds = get_harvest_seeds(Repositories.HVA, SET_SPECIFICATION, cls.begin_of_time)

    def test_get_id(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["external_id"], "7288bd68-d62b-4db0-8cea-5f189e209254")

    def test_get_files(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["files"], [])
        self.assertEqual(seeds[3]["files"], [
            {
                "mime_type": "application/pdf",
                "url": "http://testserver/api/v1/files/hva/research-outputs/d7126f6d-c412-43c8-ad2a-6acb7613917d/files/"
                       "MDIyMzRi/636835_schuldenvrij-de-weg-naar-werk_aangepast.pdf",
                "hash": "f5052b0d0d801fcd313c4395f963ab332ab3a521",
                "title": "636835_schuldenvrij-de-weg-naar-werk_aangepast.pdf",
                "copyright": None,
                "access_rights": "OpenAccess"
            }
        ])

    def test_get_url(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]["url"],
            "https://accpure.hva.nl/en/publications/7288bd68-d62b-4db0-8cea-5f189e209254"
        )
        self.assertEqual(
            seeds[3]["url"],
            "http://testserver/api/v1/files/hva/research-outputs/d7126f6d-c412-43c8-ad2a-6acb7613917d/files/MDIyMzRi/"
            "636835_schuldenvrij-de-weg-naar-werk_aangepast.pdf"
        )

    def test_get_mime_type(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]["mime_type"])
        self.assertEqual(seeds[3]["mime_type"], "application/pdf")

    def test_get_analysis_allowed(self):
        seeds = self.seeds
        self.assertFalse(seeds[0]["analysis_allowed"], "Expected closed-access to disallow analysis")
        self.assertTrue(seeds[3]["analysis_allowed"], "Expected open-access to allow analysis")

    def test_get_language(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["language"], {"metadata": "nl"})
        self.assertEqual(seeds[4]["language"], {"metadata": "en"})

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
        self.assertEqual(seeds[0]["research_object_type"], "Report")

    def test_doi(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]["doi"])
        self.assertEqual(seeds[5]["doi"], "10.1088/0031-+9120/+50/5/573")

    def test_publisher_date(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_date"], "2016-01-01")
        self.assertEqual(seeds[1]["publisher_date"], "2016-02-01")
        self.assertIsNone(seeds[5]["publisher_date"])
