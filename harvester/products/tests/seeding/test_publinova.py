from django.test import TestCase

from core.processors import HttpSeedingProcessor
from sources.factories.publinova.extraction import PublinovaMetadataResourceFactory
from products.models import Set
from products.sources.publinova import SEEDING_PHASES


class TestPublinovaProductExtraction(TestCase):

    set = None
    seeds = []

    @classmethod
    def setUpTestData(cls):
        PublinovaMetadataResourceFactory.create_common_responses()
        cls.set = Set.objects.create(name="publinova", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("publinova", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

    def test_get_record_state(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["state"], "active")

    def test_get_set(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["set"], "publinova:publinova")

    def test_get_id(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["external_id"], "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257")

    def test_get_files(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["files"], [
            "https://api.publinova.acc.surf.zooma.cloud/api/products/"
            "0b8efc72-a7a8-4635-9de9-84010e996b9e/download/41ab630b-fce0-431a-a523-078ca000c1c4",
        ])

    def test_get_language(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["language"], "unk")

    def test_get_keywords(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["keywords"], [])
        self.assertEqual(seeds[8]["keywords"], ["<script>alert('keyword script');</script>"])

    def test_get_copyright(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["copyright"], "open-access")
        self.assertEqual(seeds[1]["copyright"], "other")

    def test_get_authors(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['authors'], [
            {
                "name": "Support 1 SURF", "email": "s1@surf.nl", "dai": None,
                "isni": None, "orcid": None, "external_id": "a8986f6c-69e3-4c05-9f0a-903c554644f6"
            }
        ])

    def test_get_publishers(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publishers"], [])
        self.assertEqual(seeds[3]["publishers"], ["SURF"])

    def test_get_publisher_year(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_year"], 2023)

    def test_get_publisher_date(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_date"], "2023-03-01")
        self.assertEqual(seeds[1]["publisher_date"], "2022-09-24")

    def test_get_doi(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["doi"], "10.5117/THRM2019.3.VETH")
        self.assertEqual(seeds[1]["doi"], "10.1002/+14651858.CD010412.pub2",
                         "Output should be without prefix or whitespace in doi")
        self.assertEqual(seeds[2]["doi"], "10.1016/j.apenergy.2014.11.071")
        self.assertEqual(seeds[3]["doi"], None,
                         "strings without 10. should return NoneType")
        self.assertEqual(seeds[4]["doi"], None)

    def test_get_research_themes(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["research_product"]["research_themes"], [])
        self.assertEqual(seeds[4]["research_product"]["research_themes"], ["Economie & Management"])
