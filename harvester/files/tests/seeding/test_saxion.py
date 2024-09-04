from django.test import TestCase

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from sources.factories.saxion.extraction import SaxionOAIPMHResourceFactory
from sources.models import SaxionOAIPMHResource
from files.models import Set, FileDocument
from files.sources.saxion import SEEDING_PHASES


class TestSaxionFileSeeding(TestCase):

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
        SaxionOAIPMHResourceFactory.create_common_responses()

    def setUp(self) -> None:
        super().setUp()
        self.set = Set.objects.create(name="saxion:kenniscentra", identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })

    def test_initial_seeding(self):
        for batch in self.processor("kenniscentra", "1970-01-01T00:00:00Z"):
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
        self.assertEqual(self.set.documents.count(), 202)

    def test_delta_seeding(self):
        # Load the initial data, set all tasks as completed and create delta Resource
        initial_documents = []
        for batch in self.processor("kenniscentra", "1970-01-01T00:00:00Z"):
            for doc in batch:
                for task in doc.tasks.keys():
                    doc.pipeline[task] = {"success": True}
                doc.finish_processing()
                initial_documents.append(doc)
        # Saxion doesn't really have delta's, so we delete initial resources and create a new "delta" resource.
        SaxionOAIPMHResource.objects.all().delete()
        SaxionOAIPMHResourceFactory.create(is_initial=False, number=0)
        # Set some expectations
        become_processing_ids = {
            # Documents added by the delta
            "saxion:kenniscentra:1FC6BD0B-CE70-4D4D-83AF26E4AA012345:04d7bda7cec76d8a96bfc13ab50c18556eeb8c7e",
            "saxion:kenniscentra:1FC6BD0B-CE70-4D4D-83AF26E4AA012345:9159317f19ac15d1f2200ab36134030bc5faa36e"
        }
        # Load the delta data and see if updates have taken place
        documents = []
        for batch in self.processor("kenniscentra", "2020-01-01T00:00:00Z"):
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
        self.assertEqual(len(documents), 2, "Expected 2 additions")
        self.assertEqual(
            self.set.documents.count(), 202 + 2,
            "Expected 202 initial Documents and 2 additional Documents"
        )


class TestSaxionFileExtraction(TestCase):

    set = None
    seeds = []

    deleted = None

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })
        SaxionOAIPMHResourceFactory.create_common_responses()
        cls.set = Set.objects.create(name="saxion:kenniscentra", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("kenniscentra", "1970-01-01T00:00:00Z"):
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
            "1FC6BD0B-CE70-4D4D-83AF26E4AA0A8DC0:04d7bda7cec76d8a96bfc13ab50c18556eeb8c7e"
        )

    def test_get_set(self):
        self.assertEqual(self.seeds[0]["set"], "saxion:kenniscentra")

    def test_get_language(self):
        self.assertEqual(self.seeds[0]["language"], "en")
        self.assertEqual(self.seeds[2]["language"], "nl")

    def test_get_url(self):
        self.assertEqual(self.seeds[0]["url"], "https://resolver.saxion.nl/getfile/0CFB5656-CD05-4D48-8ADE98638765CF2E")

    def test_get_hash(self):
        self.assertEqual(self.seeds[0]["hash"], "04d7bda7cec76d8a96bfc13ab50c18556eeb8c7e")

    def test_get_mime_type(self):
        self.assertEqual(self.seeds[0]["mime_type"], "application/pdf")

    def test_get_copyright(self):
        self.assertEqual(self.seeds[0]["copyright"], "cc-by-nc-nd-40")

    def test_get_access_rights(self):
        self.assertEqual(self.seeds[0]["access_rights"], "OpenAccess")

    def test_get_product_id(self):
        self.assertEqual(self.seeds[0]["product_id"], "1FC6BD0B-CE70-4D4D-83AF26E4AA0A8DC0")

    def test_get_is_link(self):
        self.assertFalse(self.seeds[0]["is_link"])
        self.assertTrue(self.seeds[1]["is_link"])

    def test_get_provider(self):
        self.assertEqual(self.seeds[0]["provider"], {
            "ror": None,
            "external_id": None,
            "slug": "saxion",
            "name": "Saxion"
        })
