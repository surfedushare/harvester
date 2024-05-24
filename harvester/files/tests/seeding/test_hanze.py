from django.test import TestCase, override_settings

from datagrowth.configuration import register_defaults
from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from files.models import Set
from files.sources.hanze import SEEDING_PHASES
from sources.models import HanzeResearchObjectResource
from sources.factories.hanze.extraction import HanzeResearchObjectResourceFactory
from testing.cases import seeding


@override_settings(SOURCES_MIDDLEWARE_API="http://testserver/api/v1/")
class TestHanzeFileSeeding(seeding.SourceSeedingTestCase):

    entity = "files"
    source = "hanze"
    resource = HanzeResearchObjectResource
    resource_factory = HanzeResearchObjectResourceFactory
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 14)
        self.assertEqual(self.set.documents.count(), 14)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "hanze:hanze:ffffffff-3115-41bb-9d73-2a193da652ea:34c9d2735ae055acb66f3cd85c996a84efd12842",
        ])
        self.assertEqual(len(documents), 8, "Expected test to work with single page for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 14 + 1,
            "Expected 14 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 8,
            "Expected 8 Documents to have no deleted_at date and 7 with deleted_at, "
            "because second page didn't come in through the delta"
        )
        updated_title = "wtnr2_verh1_p99_113_HR_v2_Nationale_ervaringen_met_" \
                        "ondergrondse_infiltratievoorzieningen_20_jaar.pdf"
        self.assertEqual(
            self.set.documents.filter(properties__title=updated_title).count(), 1,
            "Expected title to get updated during delta harvest"
        )


@override_settings(SOURCES_MIDDLEWARE_API="http://testserver/api/v1/")
class TestHanzeFileExtraction(TestCase):

    set = None
    seeds = []

    @classmethod
    def setUpTestData(cls):
        register_defaults("global", {
            "cache_only": True
        })

        HanzeResearchObjectResourceFactory.create_common_responses()
        cls.set = Set.objects.create(name="hanze", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("hanze", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

        register_defaults("global", {
            "cache_only": False
        })

    def test_get_state(self):
        self.assertEqual(self.seeds[0]["state"], "active")

    def test_get_set(self):
        self.assertEqual(self.seeds[0]["set"], "hanze:hanze")

    def test_get_external_id(self):
        self.assertEqual(
            self.seeds[0]["external_id"],
            "01ea0ee1-a419-42ee-878b-439b44562098:01df6be8b59f65074350ca33c8eded52ea106222"
        )

    def test_get_url(self):
        self.assertEqual(
            self.seeds[0]["url"],
            "http://testserver/api/v1/files/hanze/research-outputs/01ea0ee1-a419-42ee-878b-439b44562098/"
            "files/NWU1MWM2/wtnr2_verh1_p99_113_HR_v2_Inter_nationale_ervaringen"
            "_met_ondergrondse_infiltratievoorzieningen_20_jaar.pdf"
        )

    def test_get_hash(self):
        self.assertEqual(self.seeds[0]["hash"], "01df6be8b59f65074350ca33c8eded52ea106222")

    def test_get_mime_type(self):
        self.assertEqual(self.seeds[0]["mime_type"], "application/pdf")

    def test_get_title(self):
        self.assertEqual(
            self.seeds[0]["title"],
            "wtnr2_verh1_p99_113_HR_v2_Inter_nationale_ervaringen_met_ondergrondse_infiltratievoorzieningen_20_jaar.pdf"
        )

    def test_get_access_rights(self):
        self.assertEqual(self.seeds[0]["access_rights"], "OpenAccess")
        self.assertEqual(self.seeds[2]["access_rights"], "RestrictedAccess")

    def test_get_product_id(self):
        self.assertEqual(self.seeds[0]["product_id"], "01ea0ee1-a419-42ee-878b-439b44562098")

    def test_get_is_link(self):
        self.assertFalse(self.seeds[0]["is_link"])
        self.assertTrue(self.seeds[2]["is_link"])

    def test_get_provider(self):
        self.assertEqual(self.seeds[0]["provider"], "hanze")
