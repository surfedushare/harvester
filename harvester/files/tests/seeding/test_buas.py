from django.test import TestCase

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from files.models import Set
from files.sources.buas import SEEDING_PHASES
from sources.factories.buas.extraction import BuasPureResourceFactory


class TestBuasFileExtraction(TestCase):

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

    def test_get_state(self):
        self.assertEqual(self.seeds[0]["state"], "active")

    def test_get_set(self):
        self.assertEqual(self.seeds[0]["set"], "buas:buas")

    def test_get_external_id(self):
        self.assertEqual(
            self.seeds[0]["external_id"],
            "28aca36e-17b8-48eb-a4a3-70610dbf73f6:d42e0d5475f052d4fa0ef5216fd7dcbfc3a4374d"
        )

    def test_get_url(self):
        self.assertEqual(
            self.seeds[0]["url"],
            "http://www.control-online.nl/gamesindustrie/2010/04/26/nieuw-column-op-maandag/"
        )
        self.assertEqual(
            self.seeds[2]["url"],
            "https://pure.buas.nl/ws/files/15672869/Peeters_tourismandclimatemitigation_peetersp_ed_nhtv2007.pdf"
        )

    def test_get_hash(self):
        self.assertEqual(self.seeds[0]["hash"], "d42e0d5475f052d4fa0ef5216fd7dcbfc3a4374d")

    def test_get_mime_type(self):
        self.assertEqual(self.seeds[0]["mime_type"], "text/html")
        self.assertEqual(self.seeds[2]["mime_type"], "application/pdf")

    def test_get_title(self):
        self.assertIsNone(self.seeds[0]["title"], "Expected links not to have titles")
        self.assertEqual(
            self.seeds[2]["title"],
            "Peeters_tourismandclimatemitigation_peetersp_ed_nhtv2007.pdf"
        )

    def test_get_access_rights(self):
        self.assertEqual(self.seeds[0]["access_rights"], "OpenAccess")

    def test_get_product_id(self):
        self.assertEqual(self.seeds[0]["product_id"], "28aca36e-17b8-48eb-a4a3-70610dbf73f6")

    def test_get_is_link(self):
        self.assertTrue(self.seeds[0]["is_link"])
        self.assertFalse(self.seeds[2]["is_link"])

    def test_get_provider(self):
        self.assertEqual(self.seeds[0]["provider"], "buas")
