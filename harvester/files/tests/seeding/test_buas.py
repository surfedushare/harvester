from django.test import TestCase

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from files.models import Set
from files.sources.buas import SEEDING_PHASES
from sources.factories.buas.extraction import BuasPureResourceFactory


class TestHanzeFileExtraction(TestCase):

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

    def test_get_url(self):
        self.assertEqual(
            self.seeds[0]["url"],
            "http://www.control-online.nl/gamesindustrie/2010/04/26/nieuw-column-op-maandag/"
        )
        self.assertEqual(
            self.seeds[2]["url"],
            "https://pure.buas.nl/ws/files/15672869/Peeters_tourismandclimatemitigation_peetersp_ed_nhtv2007.pdf"
        )

    def test_get_mime_type(self):
        self.assertEqual(self.seeds[0]["mime_type"], "text/html")
        self.assertEqual(self.seeds[2]["mime_type"], "application/pdf")
