from django.test import TestCase, override_settings
from django.utils.timezone import now

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from products.models import Set, ProductDocument
from products.sources.hva import SEEDING_PHASES
from sources.models import HvaPureResource
from sources.factories.hva.extraction import HvaPureResourceFactory


@override_settings(SOURCES_MIDDLEWARE_API="http://testserver/api/v1/")
class TestHvaProductSeeding(TestCase):

    @classmethod
    def setUpTestData(cls):
        HvaPureResourceFactory.create_common_responses()

    def setUp(self) -> None:
        super().setUp()
        self.set = Set.objects.create(name="hva", identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })

    def test_initial_seeding(self):
        for batch in self.processor("hva", "1970-01-01T00:00:00Z"):
            self.assertIsInstance(batch, list)
            for product in batch:
                self.assertIsInstance(product, ProductDocument)
                self.assertIsNotNone(product.identity)
                self.assertTrue(product.properties)
                self.assertTrue(product.pending_at)
        self.assertEqual(self.set.documents.count(), 20)

    def test_delta_seeding(self):
        # Load the initial data, set all tasks as completed and mark everything as deleted (delete_policy=no)
        current_time = now()
        initial_documents = []
        for batch in self.processor("hva", "1970-01-01T00:00:00Z"):
            for doc in batch:
                for task in doc.tasks.keys():
                    doc.pipeline[task] = {"success": True}
                doc.properties["state"] = ProductDocument.States.DELETED
                doc.clean()
                doc.finish_processing(current_time=current_time)
                initial_documents.append(doc)
        # HvA doesn't really have delta's, so we delete initial resources and create a new "delta" resource.
        HvaPureResource.objects.all().delete()
        HvaPureResourceFactory.create(is_initial=False, number=0)
        # Set some expectations
        become_processing_ids = {
            # Documents added by the delta
            "hva:f6b1feec-b7f1-442a-9a49-1da4cbb3646a",
        }
        # Load the delta data and see if updates have taken place
        documents = []
        for batch in self.processor("hva", "2020-01-01T00:00:00Z"):
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
        self.assertEqual(len(documents), 10, "Expected test to work with single page for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 20 + 1,
            "Expected 20 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 documented added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 10,
            "Expected 10 deleted Documents, because second page didn't come in through the delta"
        )
        self.assertEqual(
            self.set.documents.filter(properties__title="Best practices schuldhulpverlening Amsterdam").count(), 1,
            "Expected title to get updated during delta harvest"
        )


@override_settings(SOURCES_MIDDLEWARE_API="http://testserver/api/v1/")
class TestHvaProductExtraction(TestCase):

    set = None
    seeds = []

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })

        HvaPureResourceFactory.create_common_responses()
        cls.set = Set.objects.create(name="hva", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("hva", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

        register_defaults("global", {
            "cache_only": False
        })

    def test_get_id(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["external_id"], "7288bd68-d62b-4db0-8cea-5f189e209254")

    def test_get_files(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["files"], [])
        self.assertEqual(seeds[3]["files"], [
            "http://testserver/api/v1/files/hva/d7126f6d-c412-43c8-ad2a-6acb7613917d/files/"
            "MDIyMzRi/636835_schuldenvrij-de-weg-naar-werk_aangepast.pdf",
        ])

    def test_get_language(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["language"], "nl")
        self.assertEqual(seeds[4]["language"], "en")

    def test_get_title(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["title"], "Leerlingen in het Amsterdamse onderwijs")

    def test_get_description(self):
        seeds = self.seeds
        self.assertTrue(seeds[0]["description"].startswith("De relatie tussen schoolloopbanen van jongeren"))

    def test_keywords(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["keywords"], ['onderzoek', 'leerlingen', 'Amsterdam', 'schoolloopbanen', 'jongeren'])

    def test_authors_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['authors'], [
            {
                'name': 'Ruben Fukkink', 'email': None,
                'external_id': "c16dbff7-4c77-463a-9d91-933bf59bbc53",
                'dai': None, 'orcid': None, 'isni': None
            },
            {
                'name': 'Sandra van Otterloo', 'email': None,
                'external_id': "hva:person:effd42a504e9a5d3963603848288d13af3188cc5",
                'dai': None, 'orcid': None, 'isni': None
            },
            {
                'name': 'Lotje Cohen', 'email': None,
                'external_id': "hva:person:412ed1fc512e775ddca58e0655220b44c50a8b20",
                'dai': None, 'orcid': None, 'isni': None
            },
            {
                'name': 'Merel van der Wouden', 'email': None,
                'external_id': "hva:person:e3a6d0b12c0e42a2afd2811d65f512b11f947d6f",
                'dai': None, 'orcid': None, 'isni': None
            },
            {
                'name': 'Bonne Zijlstra', 'email': None,
                'external_id': "hva:person:45fec1047bbfe2dda5d740d7c4b046e85af084ae",
                'dai': None, 'orcid': None, 'isni': None
            }
        ])

    def test_publisher_year(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_year"], 2016)

    def test_research_object_type(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["research_product"]["research_object_type"], "Report")

    def test_doi(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]["doi"])
        self.assertEqual(seeds[5]["doi"], "10.1088/0031-+9120/+50/5/573")

    def test_publisher_date(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_date"], "2016-01-01")
        self.assertEqual(seeds[1]["publisher_date"], "2016-02-01")
        self.assertIsNone(seeds[5]["publisher_date"])
