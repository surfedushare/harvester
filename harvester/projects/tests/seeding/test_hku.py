from pathlib import Path

from django.conf import settings
from django.test import TestCase

from datagrowth.resources.testing import ResourceFixturesMixin

from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from testing.cases import seeding
from projects.models import Set, HkuProjectResource
from projects.sources.hku import SEEDING_PHASES


class TestHKUProjectSeeding(seeding.ResourceFixturesSeedingTestCase):

    fixtures_directory = Path(settings.BASE_DIR, "projects", "fixtures", "resources", "hku")
    resource_fixtures = ["hku-projects"]
    delta_fixtures = {
        (HkuProjectResource, 1): ("body", "hku-projects.02.pii.json")
    }

    entity = "projects"
    source = "hku"
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 10)
        self.assertEqual(self.set.documents.count(), 10)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "hku:project:6376216"
        ])
        self.assertEqual(len(documents), 2, "Expected test to work with a small sample for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 10 + 1,
            "Expected 10 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 2,
            "Expected 2 Documents to have no deleted_at date and 9 with deleted_at, "
            "because most data didn't come in through the delta"
        )
        new_title = "Transformation through Static Narrative Design"
        self.assertEqual(
            self.set.documents.filter(properties__title=new_title).count(), 1,
            "Expected title to get updated during delta harvest"
        )


class TestHKUProjectsExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["hku-projects"]
    seeds = []

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.set = Set.objects.create(name="hku", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("hku", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

    def test_get_srn(self):
        self.assertEqual(self.seeds[0]["srn"], "hku:project:6376215")

    def test_get_external_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "6376215")

    def test_get_status(self):
        self.assertEqual(self.seeds[0]["project_status"], "ongoing")
        self.assertEqual(self.seeds[6]["project_status"], "finished")

    def test_get_coordinates(self):
        self.assertEqual(self.seeds[0]["coordinates"], ["52.0958071", "5.1115789"])

    def test_get_parties(self):
        self.assertEqual(self.seeds[0]["research_project"]["parties"], [])
        self.assertEqual(self.seeds[3]["research_project"]["parties"], [
            "Universiteit van Amsterdam",
            "University Utrecht",
            "Amsterdamse Hogeschool voor de Kunsten",
            "STICHTING HOGESCHOOL VOOR DE KUNSTEN UTRECHT",
        ])

    def test_get_products(self):
        self.assertEqual(self.seeds[0]["products"], [])
        self.assertEqual(self.seeds[6]["products"], [
            "hku:product:5952225",
            "hku:product:5952144",
            "hku:product:5952143",
            "hku:product:5952142",
            "hku:product:5952132",
            "hku:product:5952117"
        ])

    def test_lambda_owners(self):
        self.assertEqual(self.seeds[0]["research_project"]["owners"], [
            {
                "external_id": "hku:person:6714229",
                "email": "hello.goodbye@hku.nl",
                "name": "Hello Goodbye"
            }
        ])
        self.assertEqual(self.seeds[5]["research_project"]["owners"], [
            {
                "external_id": "hku:person:6714394",
                "email": None,
                "name": "Klaartje Klaar"
            }
        ])
        self.assertEqual(self.seeds[6]["research_project"]["owners"], [])

    def test_lambda_contacts(self):
        self.assertEqual(self.seeds[5]["research_project"]["contacts"], [
            {
                "external_id": "hku:person:6714394",
                "email": None,
                "name": "Klaartje Klaar"
            }
        ])

    def test_persons(self):
        self.assertEqual(self.seeds[0]["persons"], [
            {
                "external_id": "hku:person:6714229",
                "email": "hello.goodbye@hku.nl",
                "name": "Hello Goodbye"
            },
            {
                "external_id": "hku:person:6698518",
                "email": "pietje-puk@hku.nl",
                "name": "Pietje Puk"
            }
        ])
        self.assertEqual(self.seeds[1]["persons"], [
            {
                "external_id": "hku:person:6699825",
                "email": "christian.bale@hku.nl",
                "name": "Christian Bale"
            }
        ])

    def test_get_keywords(self):
        self.assertEqual(self.seeds[0]["keywords"], [])
        self.assertEqual(self.seeds[1]["keywords"], ["interactieve narratieven"])
        self.assertEqual(self.seeds[4]["keywords"], [
            "design thinking",
            "technologie"
        ])

    def test_photo_url(self):
        self.assertEqual(self.seeds[0]["photo_url"], "https://octo.hku.nl/octo/repository/getfile?id=S24ERl0W1dk")
        self.assertIsNone(self.seeds[1]["photo_url"])
