from django.test import TestCase

from datagrowth.configuration import register_defaults
from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from files.models import Set
from files.sources.hku import SEEDING_PHASES
from sources.models import HkuMetadataResource
from sources.factories.hku.extraction import HkuMetadataResourceFactory
from testing.cases import seeding


class TestHkuFileSeeding(seeding.SourceSeedingTestCase):

    entity = "files"
    source = "hku"
    resource = HkuMetadataResource
    resource_factory = HkuMetadataResourceFactory
    delete_policy = DeletePolicies.NO
    has_pagination = False

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 9)
        self.assertEqual(self.set.documents.count(), 9)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "hku:hku:hku:product:1:ae5e363efafb655343e3b82476184a18cac6cc98",
        ])
        self.assertEqual(len(documents), 2, "Expected test to work with single page for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 9 + 1,
            "Expected 9 documents from initial harvest and 1 new document"
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
        updated_title = "UPDATED_HKU_lectoraat_Play_Design_Development_Nuffic_Living_Lab_model_2014.mp4"
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

    def test_get_language(self):
        self.assertEqual(self.seeds[0]["language"], "en")
        self.assertEqual(self.seeds[4]["language"], "nl")

    def test_get_mime_type(self):
        self.assertEqual(self.seeds[0]["mime_type"], "application/pdf")

    def test_get_title(self):
        self.assertEqual(
            self.seeds[0]["title"],
            "HKU_lectoraat_Play_Design_Development_Nuffic_Living_Lab_model_2014.mp4"
        )

    def test_get_product_id(self):
        self.assertEqual(self.seeds[0]["product_id"], "hku:product:5951952")
