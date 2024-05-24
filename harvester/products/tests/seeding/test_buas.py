from django.test import TestCase

from datagrowth.configuration import register_defaults
from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from products.models import Set
from products.sources.buas import SEEDING_PHASES
from sources.models import BuasPureResource
from sources.factories.buas.extraction import BuasPureResourceFactory
from testing.cases import seeding


class TestBuasProductSeeding(seeding.SourceSeedingTestCase):

    entity = "products"
    source = "buas"
    resource = BuasPureResource
    resource_factory = BuasPureResourceFactory
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 20)
        self.assertEqual(self.set.documents.count(), 20)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "buas:buas:ffffffff-efb7-44f1-82c6-e9b7f1351b96",
        ])
        self.assertEqual(len(documents), 10, "Expected test to work with single page for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 20 + 1,
            "Expected 20 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 10,
            "Expected 10 Documents to have no deleted_at date and 11 with deleted_at, "
            "because second page didn't come in through the delta"
        )
        self.assertEqual(
            self.set.documents.filter(properties__title="Notes from the greener ground").count(), 1,
            "Expected title to get updated during delta harvest"
        )


class TestBuasProductExtraction(TestCase):

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

    def test_get_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "b7b17301-7123-4113-aa8a-8391aa9d7e01")

    def test_get_files(self):
        self.assertEqual(self.seeds[0]["files"], [])
        self.assertEqual(self.seeds[1]["files"], [
            "http://www.control-online.nl/gamesindustrie/2010/04/26/nieuw-column-op-maandag/",
        ])
        self.assertEqual(self.seeds[3]["files"], [
            "https://pure.buas.nl/ws/files/15672869/Peeters_tourismandclimatemitigation_peetersp_ed_nhtv2007.pdf"
        ])

    def test_get_language(self):
        self.assertEqual(self.seeds[0]["language"], "en")
        self.assertEqual(self.seeds[4]["language"], "en")

    def test_get_title(self):
        self.assertEqual(
            self.seeds[0]["title"],
            "Edinburgh inspiring capital : ensuring world beats a path to our doors"
        )

    def test_get_description(self):
        self.assertEqual(
            self.seeds[0]["description"],
            "<p>Edinburgh inspiring capital : ensuring world beats a path to our doors</p>"
        )
        self.assertIsNone(self.seeds[1]["description"])

    def test_get_keywords(self):
        self.assertEqual(self.seeds[0]["keywords"], [
            "inspiring capital",
            "beat the world",
        ])
        self.assertEqual(self.seeds[1]["keywords"], [])

    def test_authors_property(self):
        self.assertEqual(self.seeds[0]['authors'], [
            {
                'name': 'KJ Dinnie', 'email': None, 'external_id': '6f1bbf4a-b32a-4923-9f47-bb764f3dbbde',
                'dai': None, 'orcid': None, 'isni': None
            }
        ])

    def test_publisher_year(self):
        self.assertEqual(self.seeds[0]["publisher_year"], 2012)

    def test_research_object_type(self):
        self.assertEqual(self.seeds[0]["research_product"]["research_object_type"], "Article")

    def test_publisher_date(self):
        self.assertEqual(self.seeds[0]["publisher_date"], "2012-06-07")
        self.assertEqual(self.seeds[9]["publisher_date"], "2010-01-14")
