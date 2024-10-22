from django.test import TestCase

from datagrowth.resources.testing import ResourceFixturesMixin

from core.processors import HttpSeedingProcessor
from projects.models import Set
from projects.sources.sia import SEEDING_PHASES


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
