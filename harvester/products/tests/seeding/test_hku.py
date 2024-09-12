from django.test import TestCase

from datagrowth.configuration import register_defaults
from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from products.models import Set
from products.sources.hku import SEEDING_PHASES
from sources.models import HkuMetadataResource
from sources.factories.hku.extraction import HkuMetadataResourceFactory
from testing.cases import seeding


class TestHkuProductSeeding(seeding.SourceSeedingTestCase):

    entity = "products"
    source = "hku"
    resource = HkuMetadataResource
    resource_factory = HkuMetadataResourceFactory
    delete_policy = DeletePolicies.NO
    has_pagination = False

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 10)
        self.assertEqual(self.set.documents.count(), 10)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "hku:hku:hku:product:1",
        ])
        self.assertEqual(len(documents), 2, "Expected test to work with single page for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 10 + 1,
            "Expected 10 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 2,
            "Expected 2 Documents to have no deleted_at date and 8 with deleted_at, "
            "because delta is only a subset of initial data."
        )
        updated_title = "UPDATED! Nuffic Living Lab: a trailer for an international collaboration model"
        self.assertEqual(
            self.set.documents.filter(properties__title=updated_title).count(), 1,
            "Expected title to get updated during delta harvest"
        )

    def test_empty_seeding(self):
        self.resource.objects.all().delete()
        self.resource_factory.create(is_initial=False, number=0, is_empty=True)  # delta without results
        for batch in self.processor("hku", "2020-01-01T00:00:00Z"):
            self.assertEqual(batch, [])
        self.assertEqual(self.set.documents.count(), 0)


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
                "dai": None, "orcid": None, "isni": None, "is_external": False
            },
            {
                "name": "Mic Haring", "email": "mic.haring@hku.nl", "external_id": "hku:person:6699827",
                "dai": None, "orcid": None, "isni": None, "is_external": False
            }
        ])
        self.assertEqual(self.seeds[2]['authors'], [
            {
                "name": "Ketels", "email": "n.ketels@hku.nl", "external_id": "hku:person:6699884",
                "dai": None, "orcid": None, "isni": None, "is_external": False
            }

        ])

    def test_publisher_year(self):
        self.assertEqual(self.seeds[0]["publisher_year"], 2014)

    def test_get_publisher_date(self):
        self.assertEqual(self.seeds[0]["publisher_date"], "2014-04-14")
        self.assertEqual(self.seeds[8]["publisher_date"], "2008-04-01")
