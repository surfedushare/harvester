from django.test import TestCase

from core.processors import HttpSeedingProcessor
from sharekit.tests.factories import SharekitMetadataHarvestFactory
from files.models import Set as FileSet, FileDocument
from files.sources.sharekit import SEEDING_PHASES


class TestSharekitFileSeeding(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        SharekitMetadataHarvestFactory.create_common_sharekit_responses()

    def setUp(self) -> None:
        super().setUp()
        self.set = FileSet.objects.create(name="edusources", identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })

    def test_initial_seeding(self):
        for batch in self.processor("edusources", "1970-01-01T00:00:00Z"):
            self.assertIsInstance(batch, list)
            for file_ in batch:
                self.assertIsInstance(file_, FileDocument)
                self.assertIsNotNone(file_.identity)
                self.assertTrue(file_.properties)
                self.assertTrue(file_.pending_at)
        self.assertEqual(
            self.set.documents.count(), 5 + 8,
            "Expected 5 files to get added and 8 links"
        )


class TestSharekitFileExtraction(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        SharekitMetadataHarvestFactory.create_common_sharekit_responses()

    def setUp(self) -> None:
        super().setUp()
        self.set = FileSet.objects.create(name="edusources", identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })
        self.seeds = []
        for batch in self.processor("edusources", "1970-01-01T00:00:00Z"):
            self.seeds += [doc.properties for doc in batch]

    def test_get_hash(self):
        self.assertEqual(self.seeds[0]["hash"], "0ed38cdc914e5e8a6aa1248438a1e2032a14b0de")

    def test_get_external_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "0ed38cdc914e5e8a6aa1248438a1e2032a14b0de")
