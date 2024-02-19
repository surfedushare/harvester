from django.test import TestCase

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from sources.factories.saxion.extraction import SaxionOAIPMHResourceFactory
from products.models import Set
from products.sources.saxion import SEEDING_PHASES


class TestSaxionProductExtraction(TestCase):

    set = None
    seeds = []

    deleted = None

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })
        SaxionOAIPMHResourceFactory.create_common_responses()
        cls.set = Set.objects.create(name="saxion:kenniscentra", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("kenniscentra", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]
        cls.deleted = cls.seeds[2]
        register_defaults("global", {
            "cache_only": False
        })

    def test_get_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "1FC6BD0B-CE70-4D4D-83AF26E4AA0A8DC0")
        self.assertEqual(self.deleted["external_id"], "111A6389-14FE-463E-9114DFC4868FD011")

    def test_get_set(self):
        self.assertEqual(self.seeds[0]["set"], "saxion:kenniscentra")
        self.assertEqual(self.deleted["set"], "saxion:kenniscentra")

    def test_get_provider(self):
        provider = {
            "ror": None,
            "external_id": None,
            "slug": "saxion",
            "name": "Saxion"
        }
        self.assertEqual(self.seeds[0]["provider"], provider)
        self.assertEqual(self.deleted["provider"], provider)

    def test_get_files(self):
        self.assertEqual(self.seeds[0]["files"], [
            "https://resolver.saxion.nl/getfile/0CFB5656-CD05-4D48-8ADE98638765CF2E",
            "https://resolver.saxion.nl/display_details/1FC6BD0B-CE70-4D4D-83AF26E4AA0A8DC0",
        ])
        self.assertEqual(self.deleted["files"], [])

    def test_get_language(self):
        self.assertEqual(self.seeds[0]["language"], "en")
        self.assertEqual(self.seeds[1]["language"], "nl")
        self.assertEqual(self.deleted["language"], "unk")

    def test_get_title(self):
        self.assertEqual(
            self.seeds[0]["title"],
            "Evaluation of the cognitive-motor performance of adults "
            "with Duchenne Muscular Dystrophy in a hand-related task"
        )
        self.assertIsNone(self.deleted["title"])

    def test_get_description(self):
        self.assertTrue(self.seeds[0]["description"].startswith("Duchenne muscular Dystrophy (DMD)"))
        self.assertIsNone(self.deleted["description"])

    def test_authors_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['authors'], [
            {'name': 'C (Costa) Tsunami',
             'email': None,
             'external_id': 'saxion:person:31d9369d11cfacc54d4df014572268b114c50f7c',
             'dai': None,
             'orcid': None,
             'isni': None},
        ])
        self.assertEqual(self.deleted["authors"], [])

    def test_get_publishers(self):
        self.assertEqual(self.seeds[0]["publishers"], ["Saxion University of Applied Sciences"])
        self.assertEqual(self.deleted["publishers"], [])

    def test_publisher_date(self):
        self.assertEqual(self.seeds[0]["publisher_date"], "2020-01-01")
        self.assertEqual(self.seeds[1]["publisher_date"], "2020-01-01")
        self.assertIsNone(self.deleted["publisher_date"])

    def test_publisher_year(self):
        self.assertEqual(self.seeds[0]["publisher_year"], 2020)
        self.assertIsNone(self.deleted["publisher_year"])

    def test_get_organizations(self):
        self.assertEqual(self.seeds[0]["organizations"]["root"]["name"], "Saxion")

    def test_research_object_type(self):
        self.assertEqual(self.seeds[0]["research_product"]["research_object_type"], "info:eu-repo/semantics/article")
        self.assertIsNone(self.deleted["research_product"]["research_object_type"])

    def test_get_doi(self):
        self.assertIsNone(self.seeds[0]["doi"], "DOI might not be specified")
