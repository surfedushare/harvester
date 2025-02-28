from pathlib import Path
from datetime import datetime, timedelta

from django.conf import settings
from django.test import TestCase
from django.utils.timezone import now

from datagrowth.resources.testing import ResourceFixturesMixin

from core.constants import DeletePolicies
from core.processors import HttpSeedingProcessor
from testing.cases import seeding
from projects.models import Set, HuProjectResource
from projects.sources.hu import SEEDING_PHASES, HUProjectExtractor


class TestHUProjectSeeding(seeding.ResourceFixturesSeedingTestCase):

    fixtures_directory = Path(settings.BASE_DIR, "projects", "fixtures", "resources", "hu")
    resource_fixtures = ["hu-test"]
    delta_fixtures = {
        (HuProjectResource, 1): ("body", "hu-projects.02.pii.json")
    }

    entity = "projects"
    source = "hu"
    delete_policy = DeletePolicies.NO

    def test_initial_seeding(self):
        documents = super().test_initial_seeding()
        self.assertEqual(len(documents), 368)
        self.assertEqual(self.set.documents.count(), 368)

    def test_delta_seeding(self, *args):
        documents = super().test_delta_seeding([
            "hu:project:ffffffff-7513-4004-9486-aa2d8f38215f"
        ])
        self.assertEqual(len(documents), 2, "Expected test to work with a small sample for the delta")
        self.assertEqual(
            self.set.documents.all().count(), 368 + 1,
            "Expected 368 documents from initial harvest and 1 new document"
        )
        self.assertEqual(
            self.set.documents.filter(pending_at__isnull=False).count(), 1,
            "Expected 1 document added by delta to become pending"
        )
        self.assertEqual(
            self.set.documents.filter(metadata__deleted_at=None).count(), 2,
            "Expected 2 Documents to have no deleted_at date and 367 with deleted_at, "
            "because most data didn't come in through the delta"
        )
        new_title = "Ondergewicht en Leefstijl in zorgopleidingen"
        self.assertEqual(
            self.set.documents.filter(properties__title=new_title).count(), 1,
            "Expected title to get updated during delta harvest"
        )


class TestHUProjectsExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["hu-test.json"]
    seeds = []

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.set = Set.objects.create(name="hu", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("hu", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

    def test_get_status(self):
        self.assertEqual(self.seeds[0]["project_status"], "finished")
        self.assertEqual(self.seeds[1]["project_status"], "ongoing")
        self.assertEqual(self.seeds[2]["project_status"], "finished")

    def test_raw_get_status(self):
        today = now()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        def build_test_node(start: datetime | None, end: datetime | None):
            return {
                "started_at": start.strftime("%Y-%m-%d") if start else None,
                "ended_at": end.strftime("%Y-%m-%d") if end else None,
            }

        # Preparing status
        preparing = build_test_node(tomorrow, tomorrow)
        self.assertEqual(HUProjectExtractor.get_status(preparing), "to be started")
        preparing_no_end = build_test_node(tomorrow, None)
        self.assertEqual(HUProjectExtractor.get_status(preparing_no_end), "to be started")
        preparing_invalid = build_test_node(tomorrow, yesterday)
        self.assertEqual(HUProjectExtractor.get_status(preparing_invalid), "to be started")

        # Ongoing status
        ongoing = build_test_node(yesterday, tomorrow)
        self.assertEqual(HUProjectExtractor.get_status(ongoing), "ongoing")
        ongoing_no_end = build_test_node(yesterday, None)
        self.assertEqual(HUProjectExtractor.get_status(ongoing_no_end), "ongoing")
        ongoing_no_start = build_test_node(None, tomorrow)
        self.assertEqual(HUProjectExtractor.get_status(ongoing_no_start), "ongoing")

        # Finished status
        finished = build_test_node(yesterday, yesterday)
        self.assertEqual(HUProjectExtractor.get_status(finished), "finished")
        finished_no_start = build_test_node(None, yesterday)
        self.assertEqual(HUProjectExtractor.get_status(finished_no_start), "finished")

        # Unknown status
        unknown = build_test_node(None, None)
        self.assertEqual(HUProjectExtractor.get_status(unknown), "unknown")

    def test_get_title(self):
        self.assertEqual(self.seeds[0]["title"], "360 graden newsroom")

    def test_get_started_at(self):
        self.assertEqual(self.seeds[0]["started_at"], "2022-10-01")

    def test_get_ended_at(self):
        self.assertEqual(self.seeds[0]["ended_at"], "2020-12-22")

    def test_get_photo_url(self):
        self.assertEqual(
            self.seeds[0]["photo_url"],
            "https://acceptatie.hu.nl/-/media/hu/afbeeldingen/onderzoek/projecten/360-graden-newsroom.ashx"
        )
        self.assertIsNone(self.seeds[1]["photo_url"])
