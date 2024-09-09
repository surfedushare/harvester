from django.test import TestCase

from datagrowth.configuration import register_defaults

from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from products.models import Set
from products.sources.anatomy_tool import SEEDING_PHASES
from sources.models import AnatomyToolOAIPMH
from sources.factories.anatomy_tool.extraction import AnatomyToolOAIPMHFactory
from testing.cases import seeding


class TestAnatomyToolProductSeeding(seeding.SourceSeedingTestCase):

    entity = "products"
    source = "anatomy_tool"
    resource = AnatomyToolOAIPMH
    resource_factory = AnatomyToolOAIPMHFactory
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 20)
        self.assertEqual(self.set.documents.count(), 20)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "anatomy_tool:anatomy_tool:oai:anatomytool.org:62564"
        ])
        self.assertEqual(len(documents), 10, "Expected delta to work with a single page")
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
            "Expected 6 Documents to have no deleted_at date and 10 with deleted_at, "
            "because second page didn't come in through the delta"
        )
        self.assertEqual(
            self.set.documents.filter(properties__title="Macroscopy tutorial duodenum").count(), 1,
            "Expected title to get updated during delta harvest"
        )


class TestAnatomyToolProductExtraction(TestCase):

    set = None
    seeds = []

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })
        AnatomyToolOAIPMHFactory.create_common_responses()
        cls.set = Set.objects.create(identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("anatomy_tool", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]
        register_defaults("global", {
            "cache_only": False
        })

    def test_get_language(self):
        self.assertEqual(self.seeds[0]["language"], "x-none")
        self.assertEqual(self.seeds[1]["language"], "en")

    def test_get_modified_at(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["modified_at"], "2020-10-28T02:39:34Z")

    def test_authors_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['authors'], [
            {
                "name": "O. Paul Gobée",
                "email": None,
                "external_id": None,
                "dai": None,
                "orcid": None,
                "isni": None,
                "is_external": None,
            },
            {
                "name": "Prof. X. Test",
                "email": None,
                "external_id": None,
                "dai": None,
                "orcid": None,
                "isni": None,
                "is_external": None,
            }
        ])

    def test_lom_educational_level(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["learning_material"]["lom_educational_levels"], ["HBO", "WO"])

    def test_get_files(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["files"], ["https://anatomytool.org/node/56055"])
        self.assertEqual(seeds[6]["files"], ["https://anatomytool.org/node/56176"])

    def test_get_copyright(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["copyright"], "cc-by-nc-sa-40")
        self.assertEqual(seeds[6]["copyright"], "yes")

    def test_get_keywords(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["keywords"], ['A05.6.02.001 Duodenum', 'A05.9.01.001 Pancreas'])

    def test_get_publisher_date(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_date"], "2016-06-05")
        self.assertIsNone(seeds[1]["publisher_date"])

    def test_get_publisher_year(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_year"], 2016)
        self.assertIsNone(seeds[1]["publisher_year"])
