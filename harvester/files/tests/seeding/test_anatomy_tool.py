from datagrowth.configuration import register_defaults
from django.test import TestCase

from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from sources.models import AnatomyToolOAIPMH
from sources.factories.anatomy_tool.extraction import AnatomyToolOAIPMHFactory
from files.models import Set as FileSet, FileDocument
from files.sources.anatomy_tool import SEEDING_PHASES
from testing.cases import seeding


class TestAnatomyToolFileSeeding(seeding.SourceSeedingTestCase):

    entity = "files"
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
            "anatomy_tool:anatomy_tool:oai:anatomytool.org:62564:bba7988a82ae70261e1943efe81d0b61ae20bfea",
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
            self.set.documents.filter(properties__title="Macroscopy tutorial duodenum").count(), 1,
            "Expected title to get updated during delta harvest"
        )


class TestAnatomyToolFileExtraction(TestCase):

    set = None
    seeds = []

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })
        AnatomyToolOAIPMHFactory.create_common_responses()
        cls.set = FileSet.objects.create(name="anatomy_tool", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("anatomy_tool", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]
        register_defaults("global", {
            "cache_only": False
        })

    def test_get_state(self):
        self.assertEqual(self.seeds[0]["state"], FileDocument.States.ACTIVE)

    def test_get_url(self):
        self.assertEqual(self.seeds[0]["url"],
                         "https://anatomytool.org/node/56055", "Expected to get the url of an image")
        self.assertEqual(self.seeds[1]["url"],
                         "https://anatomytool.org/node/56096", "Expected to get the url of a website")

    def test_get_hash(self):
        self.assertEqual(self.seeds[0]["hash"], "2d49dee36ce2965cd9e03d91dbd4f9ac54de770a")

    def test_get_external_id(self):
        self.assertEqual(
            self.seeds[0]["external_id"], "oai:anatomytool.org:56055:2d49dee36ce2965cd9e03d91dbd4f9ac54de770a"
        )

    def test_get_mime_type(self):
        self.assertEqual(
            self.seeds[0]["mime_type"], "image/png",
            "Expected file to copy mime_type from file data"
        )
        self.assertEqual(self.seeds[1]["mime_type"], "text/html", "Expected links to have HTML mime")

    def test_get_title(self):
        self.assertEqual(self.seeds[0]["title"], "Leiden\nPhoto Duodenum and pancreas dissection specimen\nno labels")

    def test_get_copyright(self):
        self.assertEqual(self.seeds[0]["copyright"], "cc-by-nc-sa-40",
                         "Expected file to take copyright from product")
        self.assertEqual(self.seeds[1]["copyright"], "cc-by-nc-sa-40",
                         "Expected link to take access_rights from product")
        self.assertEqual(self.seeds[2]["copyright"], "yes",
                         "Expected restricted access to propagate copyright as normal")

    def test_get_access_rights(self):
        self.assertEqual(self.seeds[0]["access_rights"], "OpenAccess",
                         "Expected file to take access_rights from source")
        self.assertEqual(self.seeds[1]["access_rights"], "OpenAccess",
                         "Expected link to take access_rights from source")
        self.assertEqual(self.seeds[2]["access_rights"], "RestrictedAccess",
                         "Expected restricted access to propagate")

    def test_product_id(self):
        self.assertEqual(self.seeds[0]["product_id"], "oai:anatomytool.org:56055")

    def test_is_link(self):
        self.assertFalse(self.seeds[0]["is_link"])
        self.assertTrue(self.seeds[1]["is_link"])

    def test_get_provider(self):
        self.assertEqual(self.seeds[0]["provider"],
                         {'ror': None, 'external_id': None, 'slug': 'anatomy_tool', 'name': 'AnatomyTOOL'})

    def test_type(self):
        self.assertEqual(self.seeds[0]["type"], "image")
        self.assertEqual(self.seeds[1]["type"], "website")
        self.assertEqual(self.seeds[7]["type"], "website")
