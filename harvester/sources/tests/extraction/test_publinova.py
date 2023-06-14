from datetime import datetime

from django.test import TestCase
from django.utils.timezone import make_aware

from harvester.utils.extraction import get_harvest_seeds
from core.constants import Repositories
from sources.factories.publinova.extraction import PublinovaMetadataResourceFactory, SET_SPECIFICATION


class TestGetHarvestSeedsPublinova(TestCase):

    begin_of_time = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.begin_of_time = make_aware(datetime(year=1970, month=1, day=1))
        PublinovaMetadataResourceFactory.create_common_responses()
        cls.seeds = get_harvest_seeds(Repositories.PUBLINOVA, SET_SPECIFICATION, cls.begin_of_time, include_no_url=True)

    def test_get_record_state(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["state"], "active")

    def test_get_id(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["external_id"], "0b8efc72-a7a8-4635-9de9-84010e996b9e")

    def test_get_files(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["files"], [
            {
                "url": "https://api.publinova.acc.surf.zooma.cloud/api/products/"
                       "0b8efc72-a7a8-4635-9de9-84010e996b9e/download/41ab630b-fce0-431a-a523-078ca000c1c4",
                "title": "Circel.jpg",
                "mime_type": "image/jpeg",
                "hash": "b1e07b1c3e68ae63abf8da023169609d50266a01",
                "copyright": None,
                "access_rights": "OpenAccess"
            }
        ])

    def test_get_url(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]["url"],
            "https://api.publinova.acc.surf.zooma.cloud/api/products/"
            "0b8efc72-a7a8-4635-9de9-84010e996b9e/download/41ab630b-fce0-431a-a523-078ca000c1c4"
        )

    def test_get_mime_type(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["mime_type"], "image/jpeg")
        self.assertIsNone(seeds[1]["mime_type"])

    def test_get_technical_type(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["technical_type"], "image")
        self.assertIsNone(seeds[1]["technical_type"])

    def test_analysis_allowed(self):
        seeds = self.seeds
        self.assertTrue(seeds[0]["analysis_allowed"])

    def test_get_language(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["language"], {"metadata": "unk"})

    def test_get_keywords(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["keywords"], [])
        self.assertEqual(seeds[8]["keywords"], ["<script>alert('keyword script');</script>"])

    def test_get_authors(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['authors'], [
            {
                "name": "Support 1 SURF", "email": "s1@surf.nl", "dai": None,
                "isni": None, "orcid": None, "external_id": "a8986f6c-69e3-4c05-9f0a-903c554644f6"
            }
        ])

    def test_get_research_themes(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["research_themes"], [])
        self.assertEqual(seeds[4]["research_themes"], ["Economie & Management"])

    def test_get_parties(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["parties"], [])
        self.assertEqual(seeds[3]["parties"], ["SURF"])

    def test_get_publisher_year(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_year"], 2023)
