from django.test import TestCase

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from products.models import Set
from products.sources.hku import SEEDING_PHASES
from sources.factories.hku.extraction import HkuMetadataResourceFactory


class TestHkuProductExtraction(TestCase):

    set = None
    seeds = []

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })

        HkuMetadataResourceFactory.create_common_responses()
        cls.set = Set.objects.create(name="hku", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("hku", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

        register_defaults("global", {
            "cache_only": False
        })

    def test_get_record_state(self):
        self.assertEqual(self.seeds[0]["state"], "active")
        self.assertEqual(self.seeds[9]["state"], "deleted")

    def test_get_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "hku:product:5951952")

    def test_get_modified_at(self):
        self.assertEqual(self.seeds[0]["modified_at"], "2023-09-02")

    def test_get_files(self):
        self.assertEqual(self.seeds[0]["files"], ["https://octo.hku.nl/octo/repository/getfile?id=xRjq_aC4sKU"])
        self.assertEqual(self.seeds[7]["files"], [], "Expected no files to show as an empty list")

    def test_get_copyright(self):
        self.assertEqual(self.seeds[0]["copyright"], "cc-by-nc-nd-40")

    def test_get_language(self):
        self.assertEqual(self.seeds[0]["language"], "en")
        self.assertEqual(self.seeds[4]["language"], "nl")

    def test_get_title(self):
        self.assertEqual(
            self.seeds[0]["title"], "Nuffic Living Lab: a trailer for an international collaboration model"
        )

    def test_get_description(self):
        self.assertTrue(
            self.seeds[0]["description"].startswith("Based upon years of experience of working in quadruple")
        )

    def test_get_keywords(self):
        self.assertEqual(self.seeds[0]["keywords"], [])
        self.assertEqual(
            self.seeds[1]["keywords"],
            [
                "HKU", "Play Design and Development", "Applied Games", "Serious Games", "Gamification", "Game Design",
                "Architecture", "Vitrivius", "Game Development", "Design Principles", "Mental Healthcare", "Moodbot"
            ]
        )

    def test_authors_property(self):
        self.assertEqual(self.seeds[0]['authors'], [], "Expected documents without persons to have no authors")
        self.assertEqual(self.seeds[1]['authors'], [
            {
                "name": "Liesbet van Roes", "email": None, "external_id": "hku:person:6699976",
                "dai": None, "orcid": None, "isni": None
            },
            {
                "name": "Mic Haring", "email": "mic.haring@hku.nl", "external_id": "hku:person:6699827",
                "dai": None, "orcid": None, "isni": None
            }
        ])
        self.assertEqual(self.seeds[2]['authors'], [
            {
                "name": "Ketels", "email": "n.ketels@hku.nl", "external_id": "hku:person:6699884",
                "dai": None, "orcid": None, "isni": None
            }

        ])

    def test_publisher_year(self):
        self.assertEqual(self.seeds[0]["publisher_year"], 2014)

    def test_get_publisher_date(self):
        self.assertEqual(self.seeds[0]["publisher_date"], "2014-04-14")
        self.assertEqual(self.seeds[8]["publisher_date"], "2008-04-01")
