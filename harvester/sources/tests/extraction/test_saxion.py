from datetime import datetime

from django.test import TestCase
from django.utils.timezone import make_aware

from harvester.utils.extraction import get_harvest_seeds
from core.constants import Repositories
from sources.factories.saxion.extraction import SaxionOAIPMHResourceFactory, SET_SPECIFICATION


class TestGetHarvestSeedsSaxion(TestCase):

    seeds = None
    begin_of_time = None
    deleted = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.begin_of_time = make_aware(datetime(year=1970, month=1, day=1))
        SaxionOAIPMHResourceFactory.create_common_responses()
        cls.seeds = get_harvest_seeds(Repositories.SAXION, SET_SPECIFICATION, cls.begin_of_time)
        cls.deleted = cls.seeds[2]

    def test_get_id(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["external_id"], "1FC6BD0B-CE70-4D4D-83AF26E4AA0A8DC0")
        self.assertEqual(self.deleted["external_id"], "111A6389-14FE-463E-9114DFC4868FD011")

    def test_get_files(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["files"], [
            {
                "mime_type": "application/pdf",
                "url": "https://resolver.saxion.nl/getfile/0CFB5656-CD05-4D48-8ADE98638765CF2E",
                "hash": "04d7bda7cec76d8a96bfc13ab50c18556eeb8c7e",
                "title": "Attachment 1",
                "copyright": "cc-by-nc-nd-40",
                "access_rights": "OpenAccess"
            },
            {
                "mime_type": "text/html",
                "url": "https://resolver.saxion.nl/display_details/1FC6BD0B-CE70-4D4D-83AF26E4AA0A8DC0",
                "hash": "9217c0675afd14154f2dd0f7e47c9ec728f0e290",
                "title": "URL 1",
                "copyright": "cc-by-nc-nd-40",
                "access_rights": "OpenAccess"
            }
        ])
        self.assertEqual(self.deleted["files"], [])

    def test_get_url(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]["url"],
            "https://resolver.saxion.nl/getfile/0CFB5656-CD05-4D48-8ADE98638765CF2E"
        )
        self.assertIsNone(self.deleted["url"])

    def test_get_mime_type(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["mime_type"], "application/pdf")
        self.assertIsNone(self.deleted["mime_type"])

    def test_get_language(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["language"], {"metadata": "en"})
        self.assertEqual(seeds[1]["language"], {"metadata": "nl"})
        self.assertEqual(self.deleted["language"], {"metadata": "unk"})

    def test_get_analysis_allowed(self):
        seeds = self.seeds
        self.assertTrue(seeds[0]["analysis_allowed"], "OpenAccess document should allow analysis")
        self.assertFalse(self.deleted["analysis_allowed"])

    def test_get_title(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]["title"],
            "Evaluation of the cognitive-motor performance of adults "
            "with Duchenne Muscular Dystrophy in a hand-related task"
        )
        self.assertIsNone(self.deleted["title"])

    def test_get_publishers(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publishers"], [
            "Saxion University of Applied Sciences"
        ])
        self.assertEqual(self.deleted["publishers"], [])

    def test_get_description(self):
        seeds = self.seeds
        self.assertTrue(seeds[0]["description"].startswith("Duchenne muscular Dystrophy (DMD)"))
        self.assertIsNone(self.deleted["description"])

    def test_authors_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['authors'], [
            {'name': 'C (Costa) Tsunami', 'email': None, 'external_id': 'saxion:saxion:31d9369d11cfacc54d4df014572268b114c50f7c', 'dai': None, 'orcid': None, 'isni': None},
        ])
        self.assertEqual(self.deleted["authors"], [])

    def test_publisher_date(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_date"], "2020-01-01")
        self.assertIsNone(self.deleted["publisher_date"])

    def test_publisher_year(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_year"], 2020)
        self.assertIsNone(self.deleted["publisher_year"])

    def test_research_object_type(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["research_object_type"], "info:eu-repo/semantics/article")
        self.assertIsNone(self.deleted["research_object_type"])

