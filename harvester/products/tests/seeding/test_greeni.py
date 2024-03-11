from django.test import TestCase

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from sources.factories.greeni.extraction import GreeniOAIPMHResourceFactory
from products.models import Set, ProductDocument
from products.sources.greeni import SEEDING_PHASES


class TestGreeniProductSeeding(TestCase):

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
                self.assertIsInstance(product, ProductDocument)
                self.assertIsNotNone(product.identity)
                self.assertTrue(product.properties)
                if product.state == ProductDocument.States.ACTIVE:
                    self.assertTrue(product.pending_at)
                    self.assertIsNone(product.finished_at)
                else:
                    self.assertIsNone(product.pending_at)
                    self.assertIsNotNone(product.finished_at)
        self.assertEqual(self.set.documents.count(), 100)

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
            "greeni:PUBVHL:oai:www.greeni.nl:VBS:2:123456",
        }
        # Load the delta data and see if updates have taken place
        documents = []
        for batch in self.processor("PUBVHL", "2020-02-10T13:08:39Z"):
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
        self.assertEqual(len(documents), 1 + 1 + 1, "Expected 1 addition, 1 update and 1 deletes")
        self.assertEqual(
            self.set.documents.count(), 100 + 1,
            "Expected 100 initial Documents and one additional Document"
        )


class TestGreeniProductExtraction(TestCase):

    set = None
    seeds = []

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
        register_defaults("global", {
            "cache_only": False
        })

    def test_get_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "oai:www.greeni.nl:VBS:2:121587")

    def test_get_set(self):
        self.assertEqual(self.seeds[0]["set"], "greeni:PUBVHL")

    def test_get_modified_at(self):
        self.assertEqual(self.seeds[0]["modified_at"], "2022-03-16")

    def test_get_provider(self):
        provider = {
            "ror": None,
            "external_id": None,
            "slug": "PUBVHL",
            "name": "Hogeschool Van Hall Larenstein"
        }
        self.assertEqual(self.seeds[0]["provider"], provider)

    def test_get_files(self):
        self.assertEqual(self.seeds[0]["files"], [
            "https://www.greeni.nl/iguana/CMS.MetaDataEditDownload.cls?file=2:121587:1",
            "https://www.greeni.nl/iguana/www.main.cls?surl=greenisearch#RecordId=2.121587",
        ])

    def test_get_language(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["language"], "nl")
        self.assertEqual(seeds[30]["language"], "en")

    def test_get_title(self):
        self.assertEqual(self.seeds[0]["title"], "Out of the box...!")

    def test_get_description(self):
        self.assertTrue(self.seeds[0]["description"].startswith("Hoe kunnen de krachten gebundeld worden"))

    def test_copyright(self):
        self.assertIsNone(self.seeds[0]["copyright"])

    def test_copyright_description(self):
        self.assertIsNone(self.seeds[0]["copyright_description"])

    def test_authors_property(self):
        self.assertEqual(self.seeds[0]['authors'], [
            {'name': 'F. Timmermans',
             'email': None,
             'external_id': "PUBVHL:person:a47515e171fc035e986276e6877a2094aed68632",
             'dai': None,
             'orcid': None,
             'isni': None},
            {'name': 'J. Oudhof',
             'email': None,
             'external_id': "PUBVHL:person:002a7f69fa093f78886994644ca0cf292c37c9ef",
             'dai': None,
             'orcid': None,
             'isni': None},
        ])

    def test_get_organizations(self):
        self.assertEqual(self.seeds[0]["organizations"]["root"]["name"], "Hogeschool Van Hall Larenstein")
        self.assertEqual(self.seeds[9]["organizations"]["root"]["name"], "Hogeschool Van Hall Larenstein")

    def test_get_publishers(self):
        self.assertEqual(self.seeds[0]["publishers"], ["VHL"])
        self.assertEqual(self.seeds[9]["publishers"], ["Agrimedia"])

    def test_publisher_year(self):
        self.assertEqual(self.seeds[0]["publisher_year"], 2010)
        self.assertEqual(self.seeds[1]["publisher_year"], 2012)
        self.assertIsNone(self.seeds[2]["publisher_year"], "Expected parse errors to be ignored")

    def test_publisher_date(self):
        self.assertEqual(self.seeds[0]["publisher_date"], "2010-01-01")
        self.assertEqual(self.seeds[1]["publisher_date"], "2012-11-02")

    def test_research_object_type(self):
        self.assertEqual(self.seeds[0]["research_product"]["research_object_type"], "info:eu-repo/semantics/book")
        self.assertIsNone(self.seeds[1]["research_product"]["research_object_type"])

    def test_get_doi(self):
        self.assertIsNone(self.seeds[0]["doi"], "DOI might not be specified")
        self.assertEqual(self.seeds[3]["doi"], "10.31715/2+018.6")
