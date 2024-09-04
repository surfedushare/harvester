from django.test import TestCase

from core.processors import HttpSeedingProcessor
from sources.factories.edurep.extraction import EdurepOAIPMHFactory
from files.models import Set as FileSet, FileDocument
from files.sources.edurep import SEEDING_PHASES


class TestEdurepFileSeeding(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        EdurepOAIPMHFactory.create_common_responses()

    def setUp(self) -> None:
        super().setUp()
        self.set = FileSet.objects.create(name="edurep", identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })

    def test_initial_seeding(self):
        for batch in self.processor("edurep", "1970-01-01T00:00:00Z"):
            self.assertIsInstance(batch, list)
            for file_ in batch:
                self.assertIsInstance(file_, FileDocument)
                self.assertIsNotNone(file_.identity)
                self.assertTrue(file_.properties)
                if file_.state == FileDocument.States.ACTIVE:
                    self.assertTrue(file_.pending_at)
                    self.assertIsNone(file_.finished_at)
                else:
                    self.assertIsNone(file_.pending_at)
                    self.assertIsNotNone(file_.finished_at)
        self.assertEqual(self.set.documents.count(), 9)

    def test_delta_seeding(self):
        # Load the initial data, set all tasks as completed and create delta Resource
        initial_documents = []
        for batch in self.processor("edurep", "1970-01-01T00:00:00Z"):
            for doc in batch:
                for task in doc.tasks.keys():
                    doc.pipeline[task] = {"success": True}
                doc.finish_processing()
                initial_documents.append(doc)
        EdurepOAIPMHFactory.create(is_initial=False, number=0)
        # Set some expectations
        become_processing_ids = {
            # Changed study_vocabulary by the delta
            "surfsharekit:oai:surfsharekit.nl:b5473dd1-8aa4-455f-b359-9af8081ce697",
            # Documents added by the delta
            "surfsharekit:oai:surfsharekit.nl:3e45b9e3-ba76-4200-a927-2902177f1f6c",
            "surfsharekit:oai:surfsharekit.nl:4842596f-fe60-40ef-8c06-4d3d6e296ba4",
        }
        # Load the delta data and see if updates have taken place
        documents = []
        for batch in self.processor("edurep", "2020-02-10T13:08:39Z"):
            self.assertIsInstance(batch, list)
            for file_ in batch:
                self.assertIsInstance(file_, FileDocument)
                self.assertIsNotNone(file_.identity)
                self.assertTrue(file_.properties)
                if file_.properties["product_id"] in become_processing_ids:
                    self.assertTrue(file_.pending_at)
                    self.assertIsNone(file_.finished_at)
                else:
                    self.assertIsNone(file_.pending_at)
                    self.assertTrue(file_.finished_at)
                documents.append(file_)
        self.assertEqual(len(documents), 2 + 1 + 1, "Expected two additions, one deletion and one update")
        self.assertEqual(
            self.set.documents.count(), 9 + 2,
            "Expected 13 initial Documents and 2 delta additions"
        )

    def test_empty_seeding(self):
        EdurepOAIPMHFactory.create(is_initial=False, number=0, is_empty=True)  # delta without results
        for batch in self.processor("edurep", "2020-02-10T13:08:39Z"):
            self.assertEqual(batch, [])
        self.assertEqual(self.set.documents.count(), 0)

    def test_deletes_seeding(self):
        EdurepOAIPMHFactory.create(is_initial=False, number=0, is_deletes=True)
        # Here we expect to harvest nothing, because deletes without existing documents in the Set lead will be ignored.
        for batch in self.processor("edurep", "2020-02-10T13:08:39Z"):
            self.assertEqual(batch, [])
        self.assertEqual(self.set.documents.count(), 0)
        # Now we'll create a pre-existing Document with the active state.
        # Based on the product_id (which is the only identifier that is known for deleted files),
        # we expect this Document to be deleted.
        seed = {
            "state": FileDocument.States.ACTIVE,
            "set": "edurep",
            "external_id": "aaa",
            "product_id": "surfsharekit:oai:surfsharekit.nl:5af0e26f-c4d2-4ddd-94ab-7dd0bd531751"
        }
        document = FileDocument.build(seed, self.set)
        document.save()
        for batch in self.processor("edurep", "2020-02-10T13:08:39Z"):
            self.assertEqual(len(batch), 1)
            doc = batch[0]
            self.assertEqual(doc.properties["state"], FileDocument.States.DELETED)
            self.assertLess(doc.metadata["created_at"], doc.metadata["deleted_at"])
        self.assertEqual(self.set.documents.count(), 1)
        document = self.set.documents.first()
        self.assertEqual(document.properties["state"], FileDocument.States.DELETED)


class TestEdurepFileExtraction(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        EdurepOAIPMHFactory.create_common_responses()

    def setUp(self) -> None:
        super().setUp()
        self.set = FileSet.objects.create(name="edurep", identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })
        self.seeds = []
        for batch in self.processor("edurep", "1970-01-01T00:00:00Z"):
            self.seeds += [doc.properties for doc in batch]

    def test_get_set(self):
        self.assertEqual(self.seeds[0]["set"], "edurep:surfsharekit")

    def test_get_hash(self):
        self.assertEqual(self.seeds[0]["hash"], "0ed38cdc914e5e8a6aa1248438a1e2032a14b0de")

    def test_get_external_id(self):
        self.assertEqual(
            self.seeds[0]["external_id"],
            "surfsharekit:oai:surfsharekit.nl:5af0e26f-c4d2-4ddd-94ab-7dd0bd531751:"
            "0ed38cdc914e5e8a6aa1248438a1e2032a14b0de"
        )

    def test_get_language(self):
        self.assertEqual(self.seeds[0]["language"], "en")
        self.assertEqual(self.seeds[2]["language"], "nl")

    def test_get_mime_type(self):
        self.assertEqual(self.seeds[0]["mime_type"],
                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.assertEqual(self.seeds[1]["mime_type"], None)
        self.assertEqual(self.seeds[2]["mime_type"], "application/x-zip-compressed")

    def test_get_url(self):
        self.assertEqual(self.seeds[0]["url"],
                         "https://surfsharekit.nl/objectstore/182216be-31a2-43c3-b7de-e5dd355b09f7")
        self.assertEqual(self.seeds[1]["url"], "https://www.youtube.com/watch?v=Zl59P5ZNX3M")

    def test_get_copyright(self):
        self.assertEqual(self.seeds[0]["copyright"], "cc-by-nc-40")
        self.assertEqual(self.seeds[1]["copyright"], "cc-by-40")
        self.assertEqual(self.seeds[2]["copyright"], "cc-by-sa-40")

    def test_get_product_id(self):
        self.assertEqual(
            self.seeds[0]["product_id"],
            "surfsharekit:oai:surfsharekit.nl:5af0e26f-c4d2-4ddd-94ab-7dd0bd531751"
        )

    def test_get_access_rights(self):
        self.assertEqual(self.seeds[0]["access_rights"], "OpenAccess")

    def test_get_is_link(self):
        self.assertEqual(self.seeds[0]["is_link"], False)
        self.assertEqual(self.seeds[6]["is_link"], True)

    def test_get_provider(self):
        self.assertEqual(
            self.seeds[0]["provider"],
            {'external_id': None, 'name': 'Edurep', 'ror': None, 'slug': None},
            "file should be DELETED and give default provider")
        self.assertEqual(
            self.seeds[1]["provider"],
            {'external_id': None, 'name': 'Edurep', 'ror': None, 'slug': None},
            "file should be INACTIVE and give default provider")
        self.assertEqual(self.seeds[2]["provider"], {'external_id': None,
                                                     'name': 'AERES Hogeschool; HAS Hogeschool; Van Hall Larenstein',
                                                     'ror': None,
                                                     'slug': None})
