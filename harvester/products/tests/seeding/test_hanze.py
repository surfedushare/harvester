from django.test import TestCase, override_settings

from datagrowth.configuration import register_defaults
from core.processors import HttpSeedingProcessor
from products.models import Set
from products.sources.hanze import SEEDING_PHASES
from sources.factories.hanze.extraction import HanzeResearchObjectResourceFactory


@override_settings(SOURCES_MIDDLEWARE_API="http://testserver/api/v1/")
class TestHanzeProductExtraction(TestCase):

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

    def test_get_record_state(self):
        self.assertEqual(self.seeds[0]["state"], "active")

    def test_get_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "01ea0ee1-a419-42ee-878b-439b44562098")

    def test_get_files(self):
        self.assertEqual(self.seeds[0]["files"], [
            "http://testserver/api/v1/files/hanze/research-outputs/01ea0ee1-a419-42ee-878b-439b44562098/"
            "files/NWU1MWM2/wtnr2_verh1_p99_113_HR_v2_Inter_nationale_ervaringen"
            "_met_ondergrondse_infiltratievoorzieningen_20_jaar.pdf"
        )

    def test_get_mime_type(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["mime_type"], "application/pdf")

    def test_get_analysis_allowed(self):
        seeds = self.seeds
        self.assertTrue(seeds[0]["analysis_allowed"], "Expected OpenAccess file to allow analysis")
        self.assertFalse(
            seeds[2]["analysis_allowed"],
            "Expected RestrictedAccess file to disallow analysis, because copyright will be unknown"
        )
        self.assertFalse(seeds[3]["analysis_allowed"], "Expected ClosedAccess file to disallow analysis")

    def test_get_language(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["language"], {"metadata": "nl"})
        self.assertEqual(seeds[1]["language"], {"metadata": "en"})

    def test_get_title(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]["title"],
            "(Inter)nationale ervaringen met ondergrondse infiltratievoorzieningen: "
            "een overzicht van 20 jaar monitoring in Nederland en een aanzet tot richtlijnen",
            "Expected subtitle to be concatenated with title"
        )
        self.assertEqual(
            seeds[2]["title"], "'Vrije plekken' en cultureel erfgoed van krimpdorpen",
            "Only expected title if subtitle is not available"
        )

    def test_get_description(self):
        seeds = self.seeds
        self.assertTrue(seeds[0]["description"].startswith("Infiltratie van afstromend regenwater is"))

    def test_keywords(self):
        seeds = self.seeds
        self.assertEqual(sorted(seeds[0]["keywords"]), [
            'Engineering(all)', 'Entrepreneurship', 'afvoer', 'infiltratie', 'ondergrond', 'regenwater',
            'stedelijke gebieden'
        ])
        self.assertEqual(sorted(seeds[1]["keywords"]), [
            '3d', 'Civil and Structural Engineering', 'disasters', 'flooding', 'overstromingen', 'rampen', 'resilience',
            'risk management', 'speerpunt energie', 'water'
        ])
        self.assertEqual(sorted(seeds[7]["keywords"]), [
            'Geography, Planning and Development', 'Liveability', 'demografische ontwikkeling', 'demography',
            'krimpgebieden', 'leefbaarheid', 'leefomgeving ', 'noord-nederland', 'northern netherlands'
        ])
        self.assertEqual(sorted(seeds[10]["keywords"]), [
            'Education', 'Honours', 'blended learning', 'community building', 'corona', 'covid-19',
            'gemeenschapsvorming', 'honours education'
        ])

    def test_authors_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['authors'], [
            {
                'name': 'Woogie Boogie',
                'email': None,
                'external_id': 'f515d64c-ae09-487f-b32d-a57a66cbecd5',
                'dai': None,
                'orcid': None,
                'isni': None
            },
            {
                'name': 'Teefje Wentel',
                'email': None,
                'external_id': 'e5c04d5d-0f00-4586-9f89-42ccc81f850f',
                'dai': None,
                'orcid': None,
                'isni': None
            }
        ])

    def test_publisher_date(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_date"], "2011-11-01")
        self.assertEqual(seeds[9]["publisher_date"], "2021-02-01")

    def test_publisher_year(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_year"], 2011)
        self.assertEqual(seeds[9]["publisher_year"], 2021)

    def test_research_object_type(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["research_object_type"], "Article")

    def test_doi(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]["doi"])
        self.assertEqual(seeds[12]["doi"], "10.1016/+j+.rser.2014.10.089")

    def test_research_theme(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["research_themes"], ["techniek"])
        self.assertEqual(seeds[14]["research_themes"], ["economie_management", "ruimtelijkeordening_planning"])
