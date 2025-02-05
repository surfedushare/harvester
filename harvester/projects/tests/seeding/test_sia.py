from pathlib import Path

from django.conf import settings
from django.test import TestCase

from datagrowth.resources.testing import ResourceFixturesMixin

from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from testing.cases import seeding
from projects.models import Set, SiaProjectDetailsResource
from projects.sources.sia import SEEDING_PHASES


class TestSIAProjectSeeding(seeding.ResourceFixturesSeedingTestCase):

    fixtures_directory = Path(settings.BASE_DIR, "projects", "fixtures", "resources", "sia")
    resource_fixtures = ["sia-test"]
    delta_fixtures = {
        (SiaProjectDetailsResource, 1): ("body", "sia-project.315b.json")
    }

    entity = "projects"
    source = "sia"
    delete_policy = DeletePolicies.TRANSIENT

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 2)
        self.assertEqual(self.set.documents.count(), 2)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "sia:sia:project:1677"
        ])
        self.assertEqual(len(documents), 2, "Expected test to work with a small sample for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 2 + 1,
            "Expected 2 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 2,
            "Expected no deleted_at dates with DeletePolicy.TRANSIENT."
        )
        new_title = "Grrrrrrrroin Injury Prevention Study (GRIP)"
        self.assertEqual(
            self.set.documents.filter(properties__title=new_title).count(), 1,
            "Expected title to get updated during delta harvest"
        )

    def test_empty_seeding(self, *args):
        # Creating the test data
        self.setup_initial_documents()
        # Test updating the initial data with no new data
        batches_list = list(self.processor(self.source, "2025-01-01T00:00:00Z"))
        self.assertEqual(batches_list, [])


class TestSIAProjectsExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["sia-test.json"]
    seeds = []

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.set = Set.objects.create(name="sia", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("sia", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

    def test_get_external_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "project:315")
        self.assertEqual(self.seeds[1]["external_id"], "project:1676")

    def test_title(self):
        self.assertEqual(self.seeds[0]["title"], "Groin Injury Prevention Study (GRIP)")
        self.assertEqual(self.seeds[1]["title"], "", "Publinova expects strings for the title field")

    def test_get_status(self):
        self.assertEqual(self.seeds[0]["project_status"], "finished")
        self.assertEqual(
            self.seeds[1]["project_status"], "unknown",
            "Expected deleted project to have unknown project status"
        )

    def test_get_parties(self):
        self.assertEqual(
            self.seeds[0]["research_project"]["parties"],
            [
                "Hogeschool van Amsterdam",
                "College van Clubartsen en Consulenten (CCC)",
                "Koninklijke Nederlandse Voetbalbond (KNVB)",
                "N.V.F.S.",
                "Stichting Nederlands Paramedisch Instituut (NPI)",
                "TNO Kwaliteit van Leven",
                "Vereniging Fysiotherapeuten binnen het Betaald Voetbal (VFBV)",
                "Vereniging voor Sportgeneeskunde (VSG)",
                "ADO Den Haag",
                "AZ",
                "BVO Sparta Rotterdam",
                "De Sportartsen Groep",
                "FC Dordrecht",
                "FC Groningen Fysiotherapie",
                "FC Utrecht",
                "Fysiotherapie Dukenburg",
                "Fysiotherapie Utrecht Oost",
                "NEC Nijmegen",
                "Paramedisch Centrum Simpelveld",
                "SC Heerenveen BVO",
                "SportmedX",
                "Stichting Betaald Voetbal Excelsior",
                "Willem II",
            ]
        )
        self.assertEqual(
            self.seeds[1]["research_project"]["parties"], [],
            "Expected deleted project to have no parties"
        )

    def test_get_sia_project_reference(self):
        self.assertEqual(self.seeds[0]["research_project"]["sia_project_reference"], "2014-01-15M")
