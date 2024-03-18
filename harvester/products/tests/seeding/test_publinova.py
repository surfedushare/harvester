from django.test import TestCase
from django.utils.timezone import now

from datagrowth.configuration import register_defaults

from core.processors import HttpSeedingProcessor
from sources.models import PublinovaMetadataResource
from sources.factories.publinova.extraction import PublinovaMetadataResourceFactory
from products.models import Set, ProductDocument
from products.sources.publinova import SEEDING_PHASES


class TestAnatomyToolProductSeeding(TestCase):

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })
        PublinovaMetadataResourceFactory.create_common_responses()

    @classmethod
    def tearDownClass(cls):
        register_defaults("global", {
            "cache_only": False
        })
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        self.set = Set.objects.create(identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })

    def test_initial_seeding(self):
        for batch in self.processor("publinova", "1970-01-01T00:00:00Z"):
            self.assertIsInstance(batch, list)
            for product in batch:
                self.assertIsInstance(product, ProductDocument)
                self.assertIsNotNone(product.identity)
                self.assertTrue(product.properties)
                if product.state == ProductDocument.States.ACTIVE:
                    self.assertTrue(product.pending_at)
                    self.assertIsNone(product.finished_at)
                else:
                    self.assertIsNone(product.pending_at)
                    self.assertIsNotNone(product.finished_at)
        self.assertEqual(self.set.documents.count(), 11, "Expected 10 products and 1 product on the second page")

    def test_delta_seeding(self):
        # Load the initial data, set all tasks as completed and mark everything as deleted (delete_policy=no)
        current_time = now()
        initial_documents = []
        for batch in self.processor("publinova", "1970-01-01T00:00:00Z"):
            for doc in batch:
                for task in doc.tasks.keys():
                    doc.pipeline[task] = {"success": True}
                doc.properties["state"] = ProductDocument.States.DELETED
                doc.clean()
                doc.finish_processing(current_time=current_time)
                initial_documents.append(doc)
        # HvA doesn't really have delta's, so we delete initial resources and create a new "delta" resource.
        PublinovaMetadataResource.objects.all().delete()
        PublinovaMetadataResourceFactory.create(is_initial=False, number=0)
        # Set some expectations
        become_processing_ids = {
            # Documents added by the delta
            "publinova:publinova:18569e78-424c-42cd-bca8-ef36acc2ab30",
        }
        # Load the delta data and see if updates have taken place
        documents = []
        for batch in self.processor("publinova", "2020-01-01T00:00:00Z"):
            self.assertIsInstance(batch, list)
            for product in batch:
                self.assertIsInstance(product, ProductDocument)
                self.assertIsNotNone(product.identity)
                self.assertTrue(product.properties)
                if product.identity in become_processing_ids:
                    self.assertTrue(product.pending_at)
                    self.assertIsNone(product.finished_at)
                else:
                    self.assertIsNone(product.pending_at)
                    self.assertTrue(product.finished_at)
                documents.append(product)
        self.assertEqual(len(documents), 11, "Expected test to work with single page of 11 products for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 11 + 1,
            "Expected 11 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 11,
            "Expected 10 Documents to have no deleted_at date and 1 with deleted_at, "
            "because second page didn't come in through the delta"
        )
        update_title = "Using a Vortex (responsibly ... really, really) | Wageningen UR"
        self.assertEqual(
            self.set.documents.filter(properties__title=update_title).count(), 1,
            "Expected title to get updated during delta harvest"
        )


class TestPublinovaProductExtraction(TestCase):

    set = None
    seeds = []

    @classmethod
    def setUpTestData(cls):
        PublinovaMetadataResourceFactory.create_common_responses()
        cls.set = Set.objects.create(name="publinova", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("publinova", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

    def test_get_record_state(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["state"], "active")

    def test_get_set(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["set"], "publinova:publinova")

    def test_get_id(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["external_id"], "5be6dfeb-b9ad-41a8-b4f5-94b9438e4257")

    def test_get_modified_at(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["modified_at"], "2023-03-28T10:17:20.000000Z")

    def test_get_files(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["files"], [
            "https://api.publinova.acc.surf.zooma.cloud/api/products/"
            "0b8efc72-a7a8-4635-9de9-84010e996b9e/download/41ab630b-fce0-431a-a523-078ca000c1c4",
        ])

    def test_get_language(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["language"], "unk")

    def test_get_keywords(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["keywords"], [])
        self.assertEqual(seeds[8]["keywords"], ["<script>alert('keyword script');</script>"])

    def test_get_copyright(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["copyright"], "open-access")
        self.assertEqual(seeds[1]["copyright"], "other")

    def test_get_authors(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['authors'], [
            {
                "name": "Support 1 SURF", "email": "s1@surf.nl", "dai": None,
                "isni": None, "orcid": None, "external_id": "a8986f6c-69e3-4c05-9f0a-903c554644f6"
            }
        ])

    def test_get_publishers(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publishers"], [])
        self.assertEqual(seeds[3]["publishers"], ["SURF"])

    def test_get_publisher_year(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_year"], 2023)

    def test_get_publisher_date(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_date"], "2023-03-01")
        self.assertEqual(seeds[1]["publisher_date"], "2022-09-24")

    def test_get_doi(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["doi"], "10.5117/THRM2019.3.VETH")
        self.assertEqual(seeds[1]["doi"], "10.1002/+14651858.CD010412.pub2",
                         "Output should be without prefix or whitespace in doi")
        self.assertEqual(seeds[2]["doi"], "10.1016/j.apenergy.2014.11.071")
        self.assertEqual(seeds[3]["doi"], None,
                         "strings without 10. should return NoneType")
        self.assertEqual(seeds[4]["doi"], None)

    def test_get_research_themes(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["research_product"]["research_themes"], [])
        self.assertEqual(seeds[4]["research_product"]["research_themes"], ["Economie & Management"])
