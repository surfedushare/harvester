from datagrowth.configuration import register_defaults
from django.test import TestCase

from core.processors import HttpSeedingProcessor
from sources.factories.anatomy_tool.extraction import AnatomyToolOAIPMHFactory
from files.models import Set as FileSet, FileDocument
from files.sources.anatomy_tool import SEEDING_PHASES


class TestAnatomyToolFileSeeding(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        register_defaults("global", {
            "cache_only": True
        })
        AnatomyToolOAIPMHFactory.create_common_anatomy_tool_responses()

    @classmethod
    def tearDownClass(cls):
        register_defaults("global", {
            "cache_only": False
        })
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        self.set = FileSet.objects.create(name="edusources", identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })

    def test_initial_seeding(self):
        for batch in self.processor("edusources", "1970-01-01T00:00:00Z"):
            self.assertIsInstance(batch, list)
            for file_ in batch:
                self.assertIsInstance(file_, FileDocument)
                self.assertIsNotNone(file_.identity)
                self.assertTrue(file_.properties)
                self.assertTrue(file_.pending_at)
        self.assertEqual(
            self.set.documents.count(), 10,
            "Expected 10 documents"
        )


class TestAnatomyToolFileExtraction(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        AnatomyToolOAIPMHFactory.create_common_anatomy_tool_responses()

    def setUp(self) -> None:
        super().setUp()
        self.set = FileSet.objects.create(name="edusources", identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })
        self.seeds = []
        for batch in self.processor("edusources", "1970-01-01T00:00:00Z"):
            self.seeds += [doc.properties for doc in batch]

    def test_get_state(self):
        self.assertEqual(self.seeds[0]["state"], FileDocument.States.ACTIVE)

    def test_get_url(self):
        self.assertEqual(self.seeds[0]["url"],
                         "https://anatomytool.org/node/56055", "Expected to get the url of an image")
        self.assertEqual(self.seeds[1]["url"],
                         "https://anatomytool.org/node/56096", "Expected to get the url of a website")

    def test_get_hash(self):
        self.assertEqual(self.seeds[0]["hash"], "cfc82b306cd64856d627b19350623c7c4752b5df")

    def test_get_external_id(self):
        self.assertEqual(
            self.seeds[0]["external_id"], "oai:anatomytool.org:56055:cfc82b306cd64856d627b19350623c7c4752b5df"
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
