from django.test import TestCase

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from sources.factories.greeni.extraction import GreeniOAIPMHResourceFactory
from files.models import Set, FileDocument
from files.sources.greeni import SEEDING_PHASES


class TestGreeniFileSeeding(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        register_defaults("global", {
            "cache_only": True
        })

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        register_defaults("global", {
            "cache_only": False
        })

    @classmethod
    def setUpTestData(cls):
        GreeniOAIPMHResourceFactory.create_common_responses()

    def setUp(self) -> None:
        super().setUp()
        self.set = Set.objects.create(name="greeni:PUBVHL", identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })

    def test_initial_seeding(self):
        for batch in self.processor("PUBVHL", "1970-01-01T00:00:00Z"):
            self.assertIsInstance(batch, list)
            for product in batch:
                self.assertIsInstance(product, FileDocument)
                self.assertIsNotNone(product.identity)
                self.assertTrue(product.properties)
                if product.state == FileDocument.States.ACTIVE:
                    self.assertTrue(product.pending_at)
                    self.assertIsNone(product.finished_at)
                else:
                    self.assertIsNone(product.pending_at)
                    self.assertIsNotNone(product.finished_at)
        self.assertEqual(self.set.documents.count(), 198)

    def test_delta_seeding(self):
        # Load the initial data, set all tasks as completed and create delta Resource
        initial_documents = []
        for batch in self.processor("PUBVHL", "1970-01-01T00:00:00Z"):
            for doc in batch:
                for task in doc.tasks.keys():
                    doc.pipeline[task] = {"success": True}
                doc.finish_processing()
                initial_documents.append(doc)
        GreeniOAIPMHResourceFactory.create(is_initial=False, number=0)
        # Set some expectations
        become_processing_ids = {
            # Documents added by the delta
            "greeni:PUBVHL:oai:www.greeni.nl:VBS:2:123456:336e32c68a8af34a8a01ef4bffc899f202160f08",
            "greeni:PUBVHL:oai:www.greeni.nl:VBS:2:123456:dd15895775332839c829d0c3d5900ac951a7aadc"
        }
        # Load the delta data and see if updates have taken place
        documents = []
        for batch in self.processor("PUBVHL", "2020-02-10T13:08:39Z"):
            self.assertIsInstance(batch, list)
            for file_ in batch:
                self.assertIsInstance(file_, FileDocument)
                self.assertIsNotNone(file_.identity)
                self.assertTrue(file_.properties)
                if file_.identity in become_processing_ids:
                    self.assertTrue(file_.pending_at)
                    self.assertIsNone(file_.finished_at)
                else:
                    self.assertIsNone(file_.pending_at)
                    self.assertTrue(file_.finished_at)
                documents.append(file_)
        self.assertEqual(len(documents), 2 + 2, "Expected 2 additions and 2 deletes")
        self.assertEqual(
            self.set.documents.count(), 198 + 2,
            "Expected 198 initial Documents and 2 additional Documents"
        )


class TestGreeniFileExtraction(TestCase):

    set = None
    seeds = []

    deleted = None

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })
        GreeniOAIPMHResourceFactory.create_common_responses()
        cls.set = Set.objects.create(name="greeni:PUBVHL", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("PUBVHL", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]
        # cls.deleted = cls.seeds[2]
        register_defaults("global", {
            "cache_only": False
        })

    def test_get_oaipmh_record_state(self):
        self.assertEqual(self.seeds[0]["state"], "active")

    def test_get_external_id(self):
        self.assertEqual(
            self.seeds[0]["external_id"],
            "oai:www.greeni.nl:VBS:2:121587:c75306b29041ba822c5310eb19d8582a9b07a585"
        )

    def test_get_set(self):
        self.assertEqual(self.seeds[0]["set"], "greeni:PUBVHL")

    def test_get_url(self):
        self.assertEqual(
            self.seeds[0]["url"],
            "https://www.greeni.nl/iguana/CMS.MetaDataEditDownload.cls?file=2:121587:1"
        )

    def test_get_hash(self):
        self.assertEqual(self.seeds[0]["hash"], "c75306b29041ba822c5310eb19d8582a9b07a585")

    def test_get_mime_type(self):
        self.assertEqual(self.seeds[0]["mime_type"], "application/pdf")

    def test_get_copyright(self):
        self.assertIsNone(self.seeds[0]["copyright"])

    def test_get_access_rights(self):
        self.assertEqual(self.seeds[0]["access_rights"], "OpenAccess")

    def test_get_product_id(self):
        self.assertEqual(self.seeds[0]["product_id"], "oai:www.greeni.nl:VBS:2:121587")

    def test_get_is_link(self):
        self.assertFalse(self.seeds[0]["is_link"])
        self.assertTrue(self.seeds[1]["is_link"])

    def test_get_provider(self):
        self.assertEqual(self.seeds[0]["provider"], {
            "ror": None,
            "external_id": None,
            "slug": "PUBVHL",
            "name": "Hogeschool Van Hall Larenstein"
        })
