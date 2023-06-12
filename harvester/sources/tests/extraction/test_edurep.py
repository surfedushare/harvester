from datetime import datetime


from django.test import TestCase
from django.utils.timezone import make_aware

from harvester.utils.extraction import get_harvest_seeds
from core.constants import Repositories
from sources.factories.edurep.extraction import EdurepJsonSearchResourceFactory, SET_SPECIFICATION


class TestGetHarvestSeedsEdurep(TestCase):

    begin_of_time = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.begin_of_time = make_aware(datetime(year=1970, month=1, day=1))
        EdurepJsonSearchResourceFactory.create_common_responses()
        cls.seeds = get_harvest_seeds(Repositories.EDUREP_JSONSEARCH, SET_SPECIFICATION, cls.begin_of_time)

    def test_get_id(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["external_id"], "jsonld-from-lom:wikiwijsmaken:41156")

    def test_state_education_level(self):
        seeds = self.seeds

        for i in range(5):
            state = seeds[i]["state"]
            lowest_educational_level = seeds[i]["lowest_educational_level"]
            if lowest_educational_level < 2:
                self.assertEqual(state, "inactive")
            else:
                self.assertEqual(state, "active")

    def test_lowest_education_level(self):
        seeds = self.seeds

        self.assertEqual(seeds[0]["lowest_educational_level"], 1,
                         "Expected file with MBO to have lowest educational level 1")
        self.assertEqual(seeds[1]["lowest_educational_level"], 1,
                         "Expected file with MBO to have lowest educational level 1")
        self.assertEqual(seeds[2]["lowest_educational_level"], 2,
                         "Expected file with HBO to have lowest educational level 2")

    def test_keywords(self):
        seeds = self.seeds
        self.assertTrue("asperge" in seeds[0]["keywords"])
        self.assertTrue("wortelen" in seeds[0]["keywords"])
        self.assertTrue("vollegrondsgroenten" in seeds[0]["keywords"])
        self.assertTrue("sperziebonen" in seeds[0]["keywords"])

    def test_copyright_description(self):
        seeds = self.seeds
        self.assertEqual(seeds[2]["copyright_description"], "https://creativecommons.org/licenses/by-sa/3.0/nl/")
        self.assertEqual(seeds[3]["copyright_description"], "http://creativecommons.org/licenses/by-nc-sa/4.0/")
        self.assertEqual(seeds[4]["copyright_description"], None)
        self.assertEqual(seeds[5]["copyright_description"], "https://creativecommons.org/licenses/by-nc-nd/3.0/nl/")

    def test_copyright(self):
        seeds = self.seeds
        self.assertEqual(seeds[2]["copyright"], "cc-by-sa-30")
        self.assertEqual(seeds[3]["copyright"], "cc-by-nc-sa-40")
        self.assertEqual(seeds[4]["copyright"], "yes")
        self.assertEqual(seeds[5]["copyright"], "cc-by-nc-nd-30")

    def test_material_types(self):
        seeds = self.seeds

        # wikiwijsmaken
        self.assertTrue("handleiding" in seeds[0]["material_types"])
        self.assertTrue("open opdracht" in seeds[0]["material_types"])
        self.assertTrue("gesloten opdracht" in seeds[0]["material_types"],
                        f"gesloten opdracht not in {seeds[3]['material_types']}")

        # l4l
        self.assertTrue("informatiebron" in seeds[3]["material_types"],
                        f"informatiebron not in {seeds[3]['material_types']}")
        self.assertEqual(len(seeds[3]["material_types"]), 1)

        # WikiwijsDelen
        self.assertTrue("informatiebron" in seeds[4]["material_types"])
        self.assertTrue("informatiebron" in seeds[5]["material_types"])

    def test_analysis_allowed(self):
        seeds = self.seeds
        self.assertEqual(seeds[2]["analysis_allowed"], True,
                         "Expected OpenAccess file to allow analysis")
        self.assertEqual(seeds[4]["analysis_allowed"], False, f"analysis is {seeds[4]['analysis_allowed']}")
        self.assertEqual(seeds[5]["analysis_allowed"], False,
                         "Expected ClosedAccess file to disallow analysis")

    def test_get_title(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["title"], "Lesmateriaal Vollegrondgroenteteelt")
        self.assertEqual(seeds[3]["title"], "Examples of assessments for boundary crossing")
        self.assertEqual(seeds[5]["title"], "Het nieuwe belichten; Film over LED-licht en diffuus licht")

    def test_get_description(self):
        seeds = self.seeds
        self.assertTrue(seeds[0]["description"].startswith("Deze lesmodule is gemaakt door docenten"))
        self.assertTrue(seeds[3]["description"].startswith("This document contains examples of assessments"))
        self.assertTrue(seeds[5]["description"].startswith("Dit project is onderdeel van het kaderprogramma"))

    def test_publisher_date(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_date"], "2013-03-27")
        self.assertEqual(seeds[5]["publisher_date"], "2017-12-14")

    def test_publisher_year(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_year"], 2013)
        self.assertEqual(seeds[5]["publisher_year"], 2017)

    def test_get_url(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]["url"],
            "http://maken.wikiwijs.nl/41156/Lesmateriaal_Vollegrondgroenteteelt"
        )

    def test_study_vocabularies(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]["study_vocabulary"],
            ['http://purl.edustandaard.nl/concept/38262d7b-2dc9-4712-b687-35b23205bf06']
        )
        self.assertEqual(
            seeds[2]["study_vocabulary"],
            []
        )

    def test_get_files(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["files"], [
            {
                'title': 'Lesmateriaal Vollegrondgroenteteelt',
                'url': 'http://maken.wikiwijs.nl/41156/Lesmateriaal_Vollegrondgroenteteelt',
                'mime_type': 'application/x-Wikiwijs-Arrangement',
                'hash': 'fbb16ac7bf46cd60244cd98879e9c28f31dec684',
                'copyright': 'https://creativecommons.org/licenses/by/3.0/nl/',
                'access_rights': 'OpenAccess'
            }
        ])
        self.assertEqual(seeds[5]["files"], [
            {
                'title': 'Het nieuwe belichten; Film over LED-licht en diffuus licht',
                'url': 'https://youtu.be/YgRjNm6T5B4',
                'mime_type': 'text/html',
                'hash': '4220f02e09da5cca7ab46c8cd354f733337eba7b',
                'copyright': 'https://creativecommons.org/licenses/by-nc-nd/3.0/nl/',
                'access_rights': 'RestrictedAccess'
            }
        ])

    def test_authors_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['authors'], [
          {
            'name': 'Buurman & Buurman',
            'email': None,
            'external_id': None,
            'dai': None,
            'orcid': None,
            'isni': None
          },
          {
            'name': 'Arthur Dent',
            'email': None,
            'external_id': None,
            'dai': None,
            'orcid': None,
            'isni': None
          },
          {
            'name': 'Geordie Laforge',
            'email': None,
            'external_id': None,
            'dai': None,
            'orcid': None,
            'isni': None
          },
          {
            'name': "Muad'dib",
            'email': None,
            'external_id': None,
            'dai': None,
            'orcid': None,
            'isni': None
          }
        ])
