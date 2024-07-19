from django.test import TestCase, override_settings

from datagrowth.configuration import register_defaults
from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from sources.models import HvaPureResource
from sources.factories.hva.extraction import HvaPureResourceFactory
from files.models import Set, FileDocument
from files.sources.hva import SEEDING_PHASES
from testing.cases import seeding


class TestHvAFileSeeding(seeding.SourceSeedingTestCase):

    entity = "files"
    source = "hva"
    resource = HvaPureResource
    resource_factory = HvaPureResourceFactory
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 11)
        self.assertEqual(self.set.documents.count(), 11)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "hva:hva:f6b1feec-b7f1-442a-9a49-1da4cbb3646a:484cf5228fad26faec3c382b410c228a8bdfe5e1",
        ])
        self.assertEqual(len(documents), 6, "Expected test to work with single page for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 11 + 1,
            "Expected 11 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 6,
            "Expected 6 Documents to have no deleted_at date and 5 with deleted_at, "
            "because second page didn't come in through the delta"
        )
        self.assertEqual(
            self.set.documents.filter(properties__title="Schuldenvrij-de-weg-naar-werk_aangepast.pdf").count(), 1,
            "Expected title to get updated during delta harvest"
        )


@override_settings(SOURCES_MIDDLEWARE_API="http://testserver/api/v1/")
class TestHvaFileExtraction(TestCase):

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

    def test_get_state(self):
        self.assertEqual(self.seeds[0]["state"], FileDocument.States.ACTIVE)
        self.assertEqual(
            self.seeds[3]["state"], FileDocument.States.ACTIVE, "Links are also active"
        )

    def test_get_external_id(self):
        self.assertEqual(
            self.seeds[0]["external_id"],
            "d7126f6d-c412-43c8-ad2a-6acb7613917d:f5052b0d0d801fcd313c4395f963ab332ab3a521"
        )
        self.assertEqual(
            self.seeds[3]["external_id"],
            "341fa580-d385-4484-9566-e94c99643e7e:54a95ef8691a8b3ac88759451ac61feeedaa14cf"
        )

    def test_get_language(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["language"], "nl")
        self.assertEqual(seeds[4]["language"], "en")

    def test_get_url(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]["url"],
            "http://testserver/api/v1/files/hva/research-outputs/d7126f6d-c412-43c8-ad2a-6acb7613917d/files/MDIyMzRi/"
            "636835_schuldenvrij-de-weg-naar-werk_aangepast.pdf"
        )
        self.assertEqual(
            seeds[3]["url"],
            "http://www.infoagepub.com/products/Joined-up-History"
        )

    def test_get_hash(self):
        self.assertEqual(self.seeds[0]["hash"], "f5052b0d0d801fcd313c4395f963ab332ab3a521")
        self.assertEqual(self.seeds[3]["hash"], "54a95ef8691a8b3ac88759451ac61feeedaa14cf")

    def test_get_mime_type(self):
        self.assertEqual(self.seeds[0]["mime_type"], "application/pdf")
        self.assertEqual(self.seeds[3]["mime_type"], "text/html", "Links should get text/html as mime_type")

    def test_get_title(self):
        self.assertEqual(self.seeds[0]["title"], "636835_schuldenvrij-de-weg-naar-werk_aangepast.pdf")
        self.assertIsNone(self.seeds[3]["title"], "Links don't have titles")

    def test_get_access_rights(self):
        self.assertEqual(self.seeds[0]["access_rights"], "OpenAccess")
        self.assertEqual(self.seeds[3]["access_rights"], "ClosedAccess")
        self.assertEqual(self.seeds[4]["access_rights"], "OpenAccess")

    def test_product_id(self):
        self.assertEqual(self.seeds[0]["product_id"], "d7126f6d-c412-43c8-ad2a-6acb7613917d")
        self.assertEqual(self.seeds[3]["product_id"], "341fa580-d385-4484-9566-e94c99643e7e")
        self.assertEqual(
            self.seeds[4]["product_id"], "341fa580-d385-4484-9566-e94c99643e7e",
            "Expected electronic versions from same research-output to share product id"
        )

    def test_is_link(self):
        self.assertFalse(self.seeds[0]["is_link"])
        self.assertTrue(self.seeds[3]["is_link"])

    def test_type(self):
        self.assertEqual(self.seeds[0]["type"], "document")
        self.assertEqual(self.seeds[3]["type"], "website", 'Expected link to be a website')
