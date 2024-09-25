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
                {"name": "Hogeschool van Amsterdam"},
                {"name": "College van Clubartsen en Consulenten (CCC)"},
                {"name": "Koninklijke Nederlandse Voetbalbond (KNVB)"},
                {"name": "N.V.F.S."},
                {"name": "Stichting Nederlands Paramedisch Instituut (NPI)"},
                {"name": "TNO Kwaliteit van Leven"},
                {"name": "Vereniging Fysiotherapeuten binnen het Betaald Voetbal (VFBV)"},
                {"name": "Vereniging voor Sportgeneeskunde (VSG)"},
                {"name": "ADO Den Haag"},
                {"name": "AZ"},
                {"name": "BVO Sparta Rotterdam"},
                {"name": "De Sportartsen Groep"},
                {"name": "FC Dordrecht"},
                {"name": "FC Groningen Fysiotherapie"},
                {"name": "FC Utrecht"},
                {"name": "Fysiotherapie Dukenburg"},
                {"name": "Fysiotherapie Utrecht Oost"},
                {"name": "NEC Nijmegen"},
                {"name": "Paramedisch Centrum Simpelveld"},
                {"name": "SC Heerenveen BVO"},
                {"name": "SportmedX"},
                {"name": "Stichting Betaald Voetbal Excelsior"},
                {"name": "Willem II"}
            ]
        )
        self.assertEqual(
            self.seeds[1]["research_project"]["parties"], [],
            "Expected deleted project to have no parties"
        )
