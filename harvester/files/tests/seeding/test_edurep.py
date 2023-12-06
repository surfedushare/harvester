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
        self.assertEqual(self.set.documents.count(), 12)


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
        self.assertEqual(self.seeds[0]["external_id"], "0ed38cdc914e5e8a6aa1248438a1e2032a14b0de")

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
        self.assertEqual(self.seeds[0]["product_id"],
                         "surfsharekit:oai:surfsharekit.nl:5af0e26f-c4d2-4ddd-94ab-7dd0bd531751")
        self.assertEqual(self.seeds[5]["product_id"],
                         "surfsharekit:oai:surfsharekit.nl:3c2b4e81-e9a1-41bc-8b6a-97bfe7e4048b")

    def test_get_access_rights(self):
        self.assertEqual(self.seeds[0]["access_rights"], "OpenAccess")

    def test_get_is_link(self):
        self.assertEqual(self.seeds[0]["is_link"], False)
        self.assertEqual(self.seeds[6]["is_link"], True)

    def test_get_provider(self):
        self.assertEqual(
            self.seeds[0]["provider"],
            {'external_id': None, 'name': None, 'ror': None, 'slug': None},
            "file should be DELETED and give no external_id")
        self.assertEqual(
            self.seeds[1]["provider"],
            {'external_id': None, 'name': None, 'ror': None, 'slug': None},
            "file should be INACTIVE and give no external_id")
        self.assertEqual(self.seeds[2]["provider"], {'external_id': None,
                                                     'name': 'AERES Hogeschool; HAS Hogeschool; Van Hall Larenstein',
                                                     'ror': None,
                                                     'slug': None})