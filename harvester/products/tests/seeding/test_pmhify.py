from django.test import TestCase

from datagrowth.configuration import register_defaults

from core.processors import HttpSeedingProcessor
from products.models import Set
from products.sources.pmhify import SEEDING_PHASES
from sources.factories.pmhify.extraction import PmhifyOAIPMHResourceFactory


class TestAnatomyToolProductExtraction(TestCase):

    set = None
    seeds = []

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })
        PmhifyOAIPMHResourceFactory.create_common_responses()
        cls.set = Set.objects.create(identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("mediasite"):
            cls.seeds += [doc.properties for doc in batch]
        register_defaults("global", {
            "cache_only": False
        })

    def test_srn(self):
        self.assertEqual(self.seeds[0]["srn"], "mediasite:mediasite:2-1:9dbff211eeb4416babb78fb0896f1a851d")
