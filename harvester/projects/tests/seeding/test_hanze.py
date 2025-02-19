from datetime import datetime, timedelta

from django.test import TestCase
from django.utils.timezone import now

from datagrowth.resources.testing import ResourceFixturesMixin

from core.processors import HttpSeedingProcessor
from projects.models import Set
from projects.sources.hanze import SEEDING_PHASES, HanzeProjectExtractProcessor


class TestHanzeProjectsExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["hanze-test.json"]
    seeds = []

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.set = Set.objects.create(name="hanze", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("hanze", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

    def test_srn(self):
        self.assertEqual(self.seeds[0]["srn"], "hanze:hanze:2236c2d4-2957-4d95-a71a-17c2845a6fd3")

    def test_get_status(self):
        self.assertEqual(self.seeds[0]["status"], "finished")
        self.assertEqual(self.seeds[4]["status"], "unknown")

    def test_raw_get_status(self):
        today = now()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        def build_test_node(start: datetime | None, end: datetime | None):
            return {
                "period": {
                    "startDate": start.strftime("%Y-%m-%d") if start else None,
                    "endDate": end.strftime("%Y-%m-%d") if end else None,
                }
            }

        # Preparing status
        preparing = build_test_node(tomorrow, tomorrow)
        self.assertEqual(HanzeProjectExtractProcessor.get_status(preparing), "to be started")
        preparing_no_end = build_test_node(tomorrow, None)
        self.assertEqual(HanzeProjectExtractProcessor.get_status(preparing_no_end), "to be started")
        preparing_invalid = build_test_node(tomorrow, yesterday)
        self.assertEqual(HanzeProjectExtractProcessor.get_status(preparing_invalid), "to be started")

        # Ongoing status
        ongoing = build_test_node(yesterday, tomorrow)
        self.assertEqual(HanzeProjectExtractProcessor.get_status(ongoing), "ongoing")
        ongoing_no_end = build_test_node(yesterday, None)
        self.assertEqual(HanzeProjectExtractProcessor.get_status(ongoing_no_end), "ongoing")
        ongoing_no_start = build_test_node(None, tomorrow)
        self.assertEqual(HanzeProjectExtractProcessor.get_status(ongoing_no_start), "ongoing")

        # Finished status
        finished = build_test_node(yesterday, yesterday)
        self.assertEqual(HanzeProjectExtractProcessor.get_status(finished), "finished")
        finished_no_start = build_test_node(None, yesterday)
        self.assertEqual(HanzeProjectExtractProcessor.get_status(finished_no_start), "finished")

        # Unknown status
        unknown = build_test_node(None, None)
        self.assertEqual(HanzeProjectExtractProcessor.get_status(unknown), "unknown")

    def test_get_title(self):
        self.assertEqual(self.seeds[0]["title"], "Ontwerpend onderzoek, coproductie in context van krimp\t")
        self.assertEqual(
            self.seeds[1]["title"],
            "Ph.D -project 'The Impact of the Hospital Environment: "
            "Understanding the Experience of the Patient Journey'",
            "Expected English title when Dutch title is missing"
        )
        self.assertEqual(
            self.seeds[2]["title"], "Water Co-Governance for Sustainable Ecosystems (Nederlands)",
            "Expected Dutch title to get preference over English title"
        )

    def test_get_description(self):
        self.assertTrue(
            self.seeds[0]["description"].startswith("ontwerpend onderzoek"),
            "Expected description to start with keyfindings when layman description is missing"
        )
        self.assertIn(
            "</br></br>Het project ‘Ontwerpend onderzoek", self.seeds[0]["description"],
            "Expected description to contain project description when keyfindings are present"
        )
        self.assertTrue(
            self.seeds[1]["description"].startswith("Patients very fear. Much sad."),
            "Expected description to start with project description when layman description and keyfindings are missing"
        )
        self.assertNotIn(
            "</br></br>", self.seeds[1]["description"],
            "Expected description to contain no newlines if only a project description is available"
        )
        self.assertIsNone(
            self.seeds[6]["description"],
            "Expected description to be None when no descriptions are present"
        )
        self.assertEqual(
            self.seeds[2]["description"], "De natuurlijke omgeving is afhankelijk van water",
            "Expected Dutch description to get preference over English"
        )

    def test_get_keywords(self):
        self.assertEqual(self.seeds[0]["keywords"], [])
        self.assertEqual(self.seeds[5]["keywords"], [
            "Healthy Ageing",
            "Health Enhancing Physical Activity",
            "Erasmus+",
            "Sport",
            "Physical Education",
            "Sport Coaching"
        ])

    def test_get_products(self):
        self.assertEqual(self.seeds[0]["products"], [])
        self.assertEqual(self.seeds[5]["products"], [
            "hanze:hanze:704dd447-825f-4708-ade5-212641c7428e",
            "hanze:hanze:ad23a0ac-4a65-4d6c-a46c-68c765fe5823",
            "hanze:hanze:a6924598-36a4-48df-8b2c-19ef8b7b2b9c",
            "hanze:hanze:c73279ff-e1fd-4d38-9808-64535392f4e7",
            "hanze:hanze:f6755774-34d3-494c-aa7d-536c9a1114b3",
            "hanze:hanze:e863e9ae-686b-43c3-91c5-94df33ab05ec",
            "hanze:hanze:de08013c-ae15-4283-bbf7-ca6d37e7e492",
            "hanze:hanze:8a71de9b-c1c1-4fcd-ba2e-652958bd1e0b"
        ])

    def test_get_persons(self):
        self.assertEqual(self.seeds[0]["persons"], [
            {"name": "Gerdy Gert Gert", "email": None, "external_id": "03157991-9fbc-4236-99d7-8c32af66f509"},
            {"name": "Kat Pax", "email": None, "external_id": "hanze:person:b7431e1498e44deb3fb129369b08d416e23f7c3b"},
        ])
        self.assertEqual(self.seeds[5]["persons"], [
            {"external_id": "e2d51cab-3b25-4890-b68f-10efeb49a9e9", "email": None, "name": "Johan de Acteur"}
        ])

    def test_get_owners(self):
        self.assertEqual(self.seeds[5]["research_project"]["owners"], [
            {
                "external_id": "e2d51cab-3b25-4890-b68f-10efeb49a9e9",
                "email": None,
                "name": "Johan de Acteur"
            }
        ])

    def test_research_theme(self):
        self.assertEqual(self.seeds[0]["research_project"]["themes"], [])
        self.assertEqual(self.seeds[1]["research_project"]["themes"], ["gezondheid"])
