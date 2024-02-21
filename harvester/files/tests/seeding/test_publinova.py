from django.test import TestCase
from django.utils.timezone import now

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from sources.models import PublinovaMetadataResource
from sources.factories.publinova.extraction import PublinovaMetadataResourceFactory
from files.models import Set, FileDocument
from files.sources.publinova import SEEDING_PHASES


class TestPublinovaFileSeeding(TestCase):

    @classmethod
    def setUpTestData(cls):
        PublinovaMetadataResourceFactory.create_common_responses()

    def setUp(self) -> None:
        super().setUp()
        self.set = Set.objects.create(name="publinova", identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })

    def test_initial_seeding(self):
        for batch in self.processor("publinova", "1970-01-01T00:00:00Z"):
            self.assertIsInstance(batch, list)
            for file_ in batch:
                self.assertIsInstance(file_, FileDocument)
                self.assertIsNotNone(file_.identity)
                self.assertTrue(file_.properties)
                self.assertTrue(file_.pending_at)
        self.assertEqual(self.set.documents.count(), 5)

    def test_delta_seeding(self):
        # Load the initial data, set all tasks as completed and mark everything as deleted (delete_policy=no)
        current_time = now()
        initial_documents = []
        for batch in self.processor("publinova", "1970-01-01T00:00:00Z"):
            for doc in batch:
                for task in doc.tasks.keys():
                    doc.pipeline[task] = {"success": True}
                doc.properties["state"] = FileDocument.States.DELETED
                doc.clean()
                doc.finish_processing(current_time=current_time)
                initial_documents.append(doc)
        # HvA doesn't really have delta's, so we delete initial resources and create a new "delta" resource.
        PublinovaMetadataResource.objects.all().delete()
        PublinovaMetadataResourceFactory.create(is_initial=False, number=0)
        # Set some expectations
        become_processing_ids = {
            # Files added by the delta
            "publinova:publinova:18569e78-424c-42cd-bca8-ef36acc2ab30:7f0d7b47dbd062d11f824f50ec5f3c150b866454",
        }
        # Load the delta data and see if updates have taken place
        documents = []
        for batch in self.processor("publinova", "2020-01-01T00:00:00Z"):
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
        self.assertEqual(len(documents), 5, "Expected test to work with single page for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 5 + 1,
            "Expected 5 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 5,
            "Expected 5 Documents to have no deleted_at date and 1 with deleted_at, "
            "because second page didn't come in through the delta"
        )
        self.assertEqual(
            self.set.documents.filter(properties__title="Vortex.jpg").count(), 1,
            "Expected title to get updated during delta harvest"
        )


class TestPublinovaFileExtraction(TestCase):

    set = None
    seeds = []

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })

        PublinovaMetadataResourceFactory.create_common_responses()
        cls.set = Set.objects.create(name="publinova", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("publinova", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

        register_defaults("global", {
            "cache_only": False
        })

    def test_get_state(self):
        self.assertEqual(self.seeds[0]["state"], FileDocument.States.ACTIVE)

    def test_get_external_id(self):
        self.assertEqual(
            self.seeds[0]["external_id"],
            "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257:b1e07b1c3e68ae63abf8da023169609d50266a01"
        )

    def test_get_url(self):
        self.assertEqual(
            self.seeds[0]["url"],
            "https://api.publinova.acc.surf.zooma.cloud/api/products/0b8efc72-a7a8-4635-9de9-84010e996b9e/download/"
            "41ab630b-fce0-431a-a523-078ca000c1c4"
        )

    def test_get_hash(self):
        self.assertEqual(self.seeds[0]["hash"], "b1e07b1c3e68ae63abf8da023169609d50266a01")

    def test_get_mime_type(self):
        self.assertEqual(self.seeds[0]["mime_type"], "image/jpeg")
        self.assertEqual(self.seeds[1]["mime_type"], "application/pdf")

    def test_get_title(self):
        self.assertEqual(self.seeds[0]["title"], "Circel.jpg")

    def test_product_id(self):
        self.assertEqual(self.seeds[0]["product_id"], "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257")

    def test_type(self):
        self.assertEqual(self.seeds[0]["type"], "image")
        self.assertEqual(self.seeds[1]["type"], "document")
