from django.test import TestCase, override_settings

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from files.models import Set
from files.sources.hanze import SEEDING_PHASES
from sources.factories.hanze.extraction import HanzeResearchObjectResourceFactory


@override_settings(SOURCES_MIDDLEWARE_API="http://testserver/api/v1/")
class TestHanzeFileExtraction(TestCase):

    set = None
    seeds = []

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })

        HanzeResearchObjectResourceFactory.create_common_responses()
        cls.set = Set.objects.create(name="hanze", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("hanze", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

        register_defaults("global", {
            "cache_only": False
        })

    def test_get_state(self):
        self.assertEqual(self.seeds[0]["state"], "active")

    def test_get_set(self):
        self.assertEqual(self.seeds[0]["set"], "hanze:hanze")

    def test_get_external_id(self):
        self.assertEqual(
            self.seeds[0]["external_id"],
            "01ea0ee1-a419-42ee-878b-439b44562098:01df6be8b59f65074350ca33c8eded52ea106222"
        )

    def test_get_url(self):
        self.assertEqual(
            self.seeds[0]["url"],
            "http://testserver/api/v1/files/hanze/research-outputs/01ea0ee1-a419-42ee-878b-439b44562098/"
            "files/NWU1MWM2/wtnr2_verh1_p99_113_HR_v2_Inter_nationale_ervaringen"
            "_met_ondergrondse_infiltratievoorzieningen_20_jaar.pdf"
        )

    def test_get_hash(self):
        self.assertEqual(self.seeds[0]["hash"], "01df6be8b59f65074350ca33c8eded52ea106222")

    def test_get_mime_type(self):
        self.assertEqual(self.seeds[0]["mime_type"], "application/pdf")

    def test_get_title(self):
        self.assertEqual(
            self.seeds[0]["title"],
            "wtnr2_verh1_p99_113_HR_v2_Inter_nationale_ervaringen_met_ondergrondse_infiltratievoorzieningen_20_jaar.pdf"
        )

    def test_get_access_rights(self):
        self.assertEqual(self.seeds[0]["access_rights"], "OpenAccess")
        self.assertEqual(self.seeds[2]["access_rights"], "RestrictedAccess")

    def test_get_product_id(self):
        self.assertEqual(self.seeds[0]["product_id"], "01ea0ee1-a419-42ee-878b-439b44562098")

    def test_get_is_link(self):
        self.assertFalse(self.seeds[0]["is_link"])
        self.assertTrue(self.seeds[2]["is_link"])

    def test_get_provider(self):
        self.assertEqual(self.seeds[0]["provider"], "hanze")
