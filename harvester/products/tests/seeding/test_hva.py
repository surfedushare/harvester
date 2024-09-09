from django.test import TestCase, override_settings

from datagrowth.configuration import register_defaults
from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from products.models import Set
from products.sources.hva import SEEDING_PHASES
from sources.models import HvaPureResource
from sources.factories.hva.extraction import HvaPureResourceFactory
from testing.cases import seeding


@override_settings(SOURCES_MIDDLEWARE_API="http://testserver/api/v1/")
class TestHvaProductSeeding(seeding.SourceSeedingTestCase):

    entity = "products"
    source = "hva"
    resource = HvaPureResource
    resource_factory = HvaPureResourceFactory
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 20)
        self.assertEqual(self.set.documents.count(), 20)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "hva:hva:f6b1feec-b7f1-442a-9a49-1da4cbb3646a",
        ])
        self.assertEqual(len(documents), 10, "Expected test to work with single page for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 20 + 1,
            "Expected 20 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 10,
            "Expected 10 Documents to have no deleted_at date and 10 with deleted_at, "
            "because second page didn't come in through the delta"
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

    def test_get_modified_at(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["modified_at"], "2018-05-01T08:21:40.498+02:00")

    def test_get_files(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["files"], [])
        self.assertEqual(seeds[3]["files"], [
            "http://testserver/api/v1/files/hva/research-outputs/d7126f6d-c412-43c8-ad2a-6acb7613917d/files/"
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
        self.assertEqual(
            sorted(seeds[0]["keywords"]),
            ['Amsterdam', 'jongeren', 'leerlingen', 'onderzoek', 'schoolloopbanen']
        )

    maxDiff = None

    def test_authors_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['authors'], [
            {
                "name": "Ruben Fukkink", "email": None,
                "external_id": "c16dbff7-4c77-463a-9d91-933bf59bbc53",
                "dai": None, "orcid": None, "isni": None, "is_external": False
            },
            {
                "name": "Sandra van Otterloo", "email": None,
                "external_id": "hva:person:effd42a504e9a5d3963603848288d13af3188cc5",
                "dai": None, "orcid": None, "isni": None, "is_external": False
            },
            {
                "name": "Lotje Cohen", "email": None,
                "external_id": "hva:person:412ed1fc512e775ddca58e0655220b44c50a8b20",
                "dai": None, "orcid": None, "isni": None, "is_external": False
            },
            {
                "name": "Merel van der Wouden", "email": None,
                "external_id": "hva:person:e3a6d0b12c0e42a2afd2811d65f512b11f947d6f",
                "dai": None, "orcid": None, "isni": None, "is_external": False
            },
            {
                "name": "Bonne Zijlstra", "email": None,
                "external_id": "hva:person:45fec1047bbfe2dda5d740d7c4b046e85af084ae",
                "dai": None, "orcid": None, "isni": None, "is_external": True
            }
        ])

    def test_get_provider(self):
        self.assertEqual(self.seeds[0]["provider"], {
            "ror": None,
            "external_id": None,
            "slug": "hva",
            "name": "Hogeschool van Amsterdam"
        })

    def test_get_publishers(self):
        self.assertEqual(self.seeds[0]["publishers"], ["Hogeschool van Amsterdam"])

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
