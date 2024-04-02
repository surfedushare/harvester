from django.test import TestCase

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from files.models import Set
from files.sources.hku import SEEDING_PHASES
from sources.factories.hku.extraction import HkuMetadataResourceFactory


class TestHkuFileExtraction(TestCase):

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

    def test_get_external_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "hku:product:5951952:3bb6b2c5cb318b7daa677e51095084c45209ae2f")

    def test_get_url(self):
        self.assertEqual(
            self.seeds[0]["url"],
            "https://octo.hku.nl/octo/repository/getfile?id=xRjq_aC4sKU"
        )

    def test_get_hash(self):
        self.assertEqual(self.seeds[0]["hash"], "3bb6b2c5cb318b7daa677e51095084c45209ae2f")

    def test_get_mime_type(self):
        self.assertEqual(self.seeds[0]["mime_type"], "application/pdf")

    def test_get_title(self):
        self.assertEqual(
            self.seeds[0]["title"],
            "HKU_lectoraat_Play_Design_Development_Nuffic_Living_Lab_model_2014.mp4"
        )

    def test_get_product_id(self):
        self.assertEqual(self.seeds[0]["product_id"], "hku:product:5951952")
