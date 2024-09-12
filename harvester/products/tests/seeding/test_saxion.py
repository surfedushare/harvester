from django.test import TestCase

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from sources.factories.saxion.extraction import SaxionOAIPMHResourceFactory
from sources.models import SaxionOAIPMHResource
from products.models import Set, ProductDocument
from products.sources.saxion import SEEDING_PHASES


class TestSaxionProductSeeding(TestCase):

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
                self.assertIsInstance(product, ProductDocument)
                self.assertIsNotNone(product.identity)
                self.assertTrue(product.properties)
                if product.state == ProductDocument.States.ACTIVE:
                    self.assertTrue(product.pending_at)
                    self.assertIsNone(product.finished_at)
                else:
                    self.assertIsNone(product.pending_at)
                    self.assertIsNotNone(product.finished_at)
        self.assertEqual(self.set.documents.count(), 200)

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
            "saxion:kenniscentra:1FC6BD0B-CE70-4D4D-83AF26E4AA012345",
        }
        # Load the delta data and see if updates have taken place
        documents = []
        for batch in self.processor("kenniscentra", "2020-01-01T00:00:00Z"):
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
        self.assertEqual(len(documents), 1 + 1, "Expected 1 addition, 1 update")
        self.assertEqual(
            self.set.documents.count(), 200 + 1,
            "Expected 200 initial Documents and one additional Document"
        )


class TestSaxionProductExtraction(TestCase):

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
        cls.deleted = cls.seeds[2]
        register_defaults("global", {
            "cache_only": False
        })

    def test_get_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "1FC6BD0B-CE70-4D4D-83AF26E4AA0A8DC0")
        self.assertEqual(self.deleted["external_id"], "111A6389-14FE-463E-9114DFC4868FD011")

    def test_get_set(self):
        self.assertEqual(self.seeds[0]["set"], "saxion:kenniscentra")
        self.assertEqual(self.deleted["set"], "saxion:kenniscentra")

    def test_get_modified_at(self):
        self.assertEqual(self.seeds[0]["modified_at"], "2021-01-26")

    def test_get_provider(self):
        provider = {
            "ror": None,
            "external_id": None,
            "slug": "saxion",
            "name": "Saxion"
        }
        self.assertEqual(self.seeds[0]["provider"], provider)
        self.assertEqual(self.deleted["provider"], provider)

    def test_get_files(self):
        self.assertEqual(self.seeds[0]["files"], [
            "https://resolver.saxion.nl/getfile/0CFB5656-CD05-4D48-8ADE98638765CF2E",
            "https://resolver.saxion.nl/display_details/1FC6BD0B-CE70-4D4D-83AF26E4AA0A8DC0",
        ])
        self.assertEqual(self.deleted["files"], [])

    def test_get_language(self):
        self.assertEqual(self.seeds[0]["language"], "en")
        self.assertEqual(self.seeds[1]["language"], "nl")
        self.assertIsNone(self.deleted["language"])

    def test_get_title(self):
        self.assertEqual(
            self.seeds[0]["title"],
            "Evaluation of the cognitive-motor performance of adults "
            "with Duchenne Muscular Dystrophy in a hand-related task"
        )
        self.assertIsNone(self.deleted["title"])

    def test_get_description(self):
        self.assertTrue(self.seeds[0]["description"].startswith("Duchenne muscular Dystrophy (DMD)"))
        self.assertIsNone(self.deleted["description"])

    def test_copyright(self):
        self.assertEqual(self.seeds[0]["copyright"], "cc-by-nc-nd-40")
        self.assertIsNone(self.deleted["copyright"])

    def test_copyright_description(self):
        self.assertEqual(self.seeds[0]["copyright_description"], "https://creativecommons.org/licenses/by-nc-nd/4.0")
        self.assertIsNone(self.deleted["copyright_description"])

    def test_authors_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['authors'], [
            {
                "name": "C (Costa) Tsunami",
                "email": None,
                "external_id": "saxion:person:31d9369d11cfacc54d4df014572268b114c50f7c",
                "dai": None,
                "orcid": None,
                "isni": None,
                "is_external": None,
            },
        ])
        self.assertEqual(self.deleted["authors"], [])

    def test_get_publishers(self):
        self.assertEqual(self.seeds[0]["publishers"], ["Saxion University of Applied Sciences"])
        self.assertEqual(self.deleted["publishers"], [])

    def test_publisher_date(self):
        self.assertEqual(self.seeds[0]["publisher_date"], "2020-01-01")
        self.assertEqual(self.seeds[1]["publisher_date"], "2020-01-01")
        self.assertIsNone(self.deleted["publisher_date"])

    def test_publisher_year(self):
        self.assertEqual(self.seeds[0]["publisher_year"], 2020)
        self.assertIsNone(self.deleted["publisher_year"])

    def test_get_organizations(self):
        self.assertEqual(self.seeds[0]["organizations"]["root"]["name"], "Saxion")

    def test_research_object_type(self):
        self.assertEqual(self.seeds[0]["research_product"]["research_object_type"], "info:eu-repo/semantics/article")
        self.assertIsNone(self.deleted["research_product"]["research_object_type"])

    def test_get_doi(self):
        self.assertIsNone(self.seeds[0]["doi"], "DOI might not be specified")
