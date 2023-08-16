from django.test import TestCase

from core.processors import HttpSeedingProcessor
from sharekit.tests.factories import SharekitMetadataHarvestFactory
from files.models import Set as FileSet, FileDocument
from files.sources.sharekit import SEEDING_PHASES


class TestHttpSeedingProcessorFiles(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        SharekitMetadataHarvestFactory.create_common_sharekit_responses()

    def setUp(self) -> None:
        super().setUp()
        self.set = FileSet.objects.create(name="edusources", identifier="srn")

    def test_initial_seeding_files(self):
        processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })

        files = processor("edusources", "1970-01-01T00:00:00Z")
        for batch in files:
            self.assertIsInstance(batch, list)
            for file_ in batch:
                self.assertIsInstance(file_, FileDocument)
                self.assertIsNotNone(file_.identity)
                self.assertTrue(file_.properties)
        self.assertEqual(
            self.set.documents.count(), 5 + 8,
            "Expected 5 files to get added and 8 links"
        )
