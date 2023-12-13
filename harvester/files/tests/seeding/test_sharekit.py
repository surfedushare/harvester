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
        self.assertEqual(len(documents), 3 + 3 + 0, "Expected three additions, three deletions and no (file) updates")
        self.assertEqual(
            self.set.documents.count(), 5 + 11,
            "Expected 5 files to get added and 11 links"
        )

    def test_empty_seeding(self):
        SharekitMetadataHarvestFactory.create(is_initial=False, number=0, is_empty=True)  # delta without results
        for batch in self.processor("edusources", "2020-02-10T13:08:39Z"):
            self.assertEqual(batch, [])
        self.assertEqual(self.set.documents.count(), 0)

    def test_deletes_seeding(self):
        SharekitMetadataHarvestFactory.create(is_initial=False, number=0, is_deletes=True)
        # Here we expect to harvest nothing, because deletes without existing documents in the Set lead will be ignored.
        for batch in self.processor("edusources", "2020-02-10T13:08:39Z"):
            self.assertEqual(batch, [])
        self.assertEqual(self.set.documents.count(), 0)
        # Now we'll create a pre-existing Document with the active state.
        # Based on the product_id (which is the only identifier that is known for deleted files),
        # we expect this Document to be deleted.
        seed = {
            "state": "active",
            "set": "edusources",
            "external_id": "aaa",
            "parent_id": "d8a7a2af-b542-4f82-864b-9896addcf9c2"
        }
        document = FileDocument.build(seed, self.set)
        document.save()
        for batch in self.processor("edusources", "2020-02-10T13:08:39Z"):
            self.assertEqual(len(batch), 1)
            doc = batch[0]
            self.assertEqual(doc.properties["state"], FileDocument.States.DELETED)
            self.assertLess(doc.metadata["created_at"], doc.metadata["deleted_at"])
        self.assertEqual(self.set.documents.count(), 1)


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

    def test_get_state(self):
        self.assertEqual(self.seeds[0]["state"], FileDocument.States.ACTIVE)

    def test_get_url(self):
        self.assertEqual(self.seeds[0]["url"],
                         "https://surfsharekit.nl/objectstore/182216be-31a2-43c3-b7de-e5dd355b09f7")
        self.assertEqual(self.seeds[1]["url"],
                         "https://www.youtube.com/watch?v=Zl59P5ZNX3M")

    def test_get_hash(self):
        self.assertEqual(self.seeds[0]["hash"], "0ed38cdc914e5e8a6aa1248438a1e2032a14b0de")

    def test_get_external_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "0ed38cdc914e5e8a6aa1248438a1e2032a14b0de")

    def test_get_mime_type(self):
        self.assertEqual(
            self.seeds[0]["mime_type"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "Expected file to copy mime_type from file data"
        )
        self.assertEqual(self.seeds[1]["mime_type"], "text/html", "Expected links to have HTML mime")

    def test_get_title(self):
        self.assertEqual(self.seeds[0]["title"], "40. Exercises 5.docx")
        self.assertIsNone(self.seeds[1]["title"], "Expected links to have no title")

    def test_get_copyright(self):
        self.assertEqual(self.seeds[0]["copyright"], "cc-by-nc-40",
                         "Expected file to take copyright from product")
        self.assertEqual(self.seeds[1]["copyright"], "cc-by-40",
                         "Expected link to take access_rights from product")
        self.assertEqual(self.seeds[2]["copyright"], "cc-by-sa-40",
                         "Expected restricted access to propagate copyright as normal")

    def test_get_access_rights(self):
        self.assertEqual(self.seeds[0]["access_rights"], "OpenAccess",
                         "Expected file to take access_rights from source")
        self.assertEqual(self.seeds[1]["access_rights"], "OpenAccess",
                         "Expected link to take access_rights from source")
        self.assertEqual(self.seeds[2]["access_rights"], "RestrictedAccess",
                         "Expected restricted access to propagate")

    def test_product_id(self):
        self.assertEqual(self.seeds[0]["product_id"], "5af0e26f-c4d2-4ddd-94ab-7dd0bd531751")

    def test_is_link(self):
        self.assertFalse(self.seeds[0]["is_link"])
        self.assertTrue(self.seeds[1]["is_link"])

    def test_get_provider(self):
        self.assertEqual(self.seeds[0]["provider"], "SURFnet")
        self.assertEqual(self.seeds[5]["provider"], "Stimuleringsregeling Open en Online Onderwijs")

    def test_type(self):
        self.assertEqual(self.seeds[0]["type"], "document")
        self.assertEqual(self.seeds[1]["type"], "website", "Expected all links to be typed as website")
        self.assertEqual(self.seeds[7]["type"], "unknown", "Expected 'unknown' for missing mime types")
