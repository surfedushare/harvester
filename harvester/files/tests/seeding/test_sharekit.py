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

    def test_delta_seeding(self):
        # Load the initial data, set all tasks as completed and create delta Resource
        initial_documents = []
        for batch in self.processor("edusources", "1970-01-01T00:00:00Z"):
            for doc in batch:
                for task in doc.tasks.keys():
                    doc.pipeline[task] = {"success": True}
                doc.finish_processing()
                initial_documents.append(doc)
        SharekitMetadataHarvestFactory.create(is_initial=False, number=0)
        # Set some expectations
        become_processing_product_ids = {
            "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257",  # Changed study_vocabulary by the delta
            # Documents added by the delta
            "3e45b9e3-ba76-4200-a927-2902177f1f6c",
            "4842596f-fe60-40ef-8c06-4d3d6e296ba4",
            "f4e867ba-0bd0-489a-824a-752038dfee63",
        }
        # Load the delta data and see if updates have taken place
        documents = []
        for batch in self.processor("edusources", "2020-02-10T13:08:39Z"):
            self.assertIsInstance(batch, list)
            # import json; print(json.dumps([doc.properties for doc in batch], indent=4))
            for file_ in batch:
                self.assertIsInstance(file_, FileDocument)
                self.assertIsNotNone(file_.identity)
                self.assertTrue(file_.properties)
                if file_.properties["product_id"] in become_processing_product_ids:
                    self.assertTrue(file_.pending_at)
                    self.assertIsNone(file_.finished_at)
                else:
                    self.assertIsNone(file_.pending_at)
                    self.assertTrue(file_.finished_at)
                documents.append(file_)
        self.assertEqual(len(documents), 3 + 5 + 1, "Expected three additions, five deletions and one update")
        self.assertEqual(
            self.set.documents.count(), 5 + 11,
            "Expected 5 files to get added and 11 links"
        )

    def test_empty_seeding(self):
        SharekitMetadataHarvestFactory.create(is_initial=False, number=0, is_empty=True)  # delta without results
        for batch in self.processor("edusources", "2020-02-10T13:08:39Z"):
            self.assertEqual(batch, [])
        self.assertEqual(self.set.documents.count(), 0)


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
