from pathlib import Path

from django.conf import settings
from django.test import TestCase

from datagrowth.resources.testing import ResourceFixturesMixin

from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from testing.cases import seeding
from persons.models import Set, HvaPersonResource
from persons.sources.hva import SEEDING_PHASES


class TestHvaPersonSeeding(seeding.ResourceFixturesSeedingTestCase):

    fixtures_directory = Path(settings.BASE_DIR, "persons", "fixtures", "resources", "hva")
    resource_fixtures = ["hva-persons.json"]
    delta_fixtures = {
        (HvaPersonResource, 1): ("body", "hva-persons.02.json"),
    }

    entity = "persons"
    source = "hva"
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 2)
        self.assertEqual(self.set.documents.count(), 2)

    def test_delta_seeding(self, *args) -> None:
        documents = super().test_delta_seeding([
            "hva:person:afa498d2-5e47-4672-b840-a2593375e6eb"
        ])
        self.assertEqual(len(documents), 2, "Expected test to work with 2 documents from the delta")
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
            "Expected 2 Documents to have no deleted_at date and 1 with deleted_at"
        )
        new_job_title = "Senior Lecturer Plus"
        self.assertEqual(
            self.set.documents.filter(properties__job_title=new_job_title).count(), 1,
            "Expected name to get updated during delta harvest"
        )


class TestHvaPersonExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["hva-persons.json"]
    seeds = []

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.set = Set.objects.create(name="hva", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("hva", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

    def test_get_srn(self):
        self.assertEqual(self.seeds[0]["srn"], "hva:person:af0b3aa3-054c-4068-9aad-506be254e6e9")

    def test_get_email(self):
        self.assertEqual(self.seeds[0]["sensitive"]["email"], "pietje-puk@acc.hva.nl")

    def test_get_name(self):
        self.assertEqual(self.seeds[0]["author"]["name"], "Pietje Puk")

    def test_get_orcid(self):
        self.assertIsNone(self.seeds[0]["researcher"]["orcid"])
        self.assertEqual(self.seeds[1]["researcher"]["orcid"], "0000-0001-7063-9748")

    def test_get_isni(self):
        self.assertIsNone(
            self.seeds[0]["author"]["isni"],
            "According to Jasper Bedaux in an email on 15th Feb 2023 Hva won't pass along ISNI."
        )

    def test_get_is_employed(self):
        self.skipTest(
            "According to Jasper Bedaux in an email on 6th March 2023 HvA won't pass along non-employed people"
        )

    def test_get_job_title(self):
        self.assertEqual(self.seeds[0]["job_title"], "Senior Lecturer")
        self.assertIsNone(
            self.seeds[1]["job_title"],
            "Missing job titles in staffOrganizationAssociation objects should return None"
        )
