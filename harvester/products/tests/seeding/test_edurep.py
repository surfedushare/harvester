from django.test import TestCase

from core.processors import HttpSeedingProcessor
from products.models import Set, ProductDocument
from products.sources.edurep import SEEDING_PHASES
from sources.factories.edurep.extraction import EdurepOAIPMHFactory


class TestEdurepProductSeeding(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        EdurepOAIPMHFactory.create_common_responses()

    def setUp(self) -> None:
        super().setUp()
        self.set = Set.objects.create(name="edurep", identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })

    def test_initial_seeding(self):
        for batch in self.processor("edurep", "1970-01-01T00:00:00Z"):
            self.assertIsInstance(batch, list)
            for file_ in batch:
                self.assertIsInstance(file_, ProductDocument)
                self.assertIsNotNone(file_.identity)
                self.assertTrue(file_.properties)
                self.assertTrue(file_.pending_at)
        self.assertEqual(self.set.documents.count(), 12)

    def test_delta_seeding(self):
        self.skipTest("to be tested")

    def test_empty_seeding(self):
        self.skipTest("to be tested")


class TestEdurepProductExtraction(TestCase):

    set = None
    seeds = []

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        EdurepOAIPMHFactory.create_common_responses(include_delta=True)
        cls.set = Set.objects.create(name="edurep", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("edurep", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]
        for batch in processor("edurep", "2020-02-10T13:08:39Z"):
            cls.seeds += [doc.properties for doc in batch]



    def test_authors_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[3]['authors'], [
            {'name': 'Ruud Kok', 'email': None, 'external_id': None, 'dai': None, 'orcid': None, 'isni': None}
        ])

    def test_publishers_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[3]['publishers'], ['AERES Hogeschool; HAS Hogeschool; Van Hall Larenstein'])
        self.assertEqual(seeds[5]['publishers'], ['SURFnet'])
        self.assertEqual(seeds[16]['publishers'], ['Erasmus Medisch Centrum'])

    def test_consortium(self):
        seeds = self.seeds
        self.assertEqual(seeds[3]['learning_material']['consortium'], None)
        self.assertEqual(seeds[16]['learning_material']['consortium'], 'HBO Verpleegkunde')

    def test_organizations(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]['organizations']['root']['name'])
        self.assertEqual(
            seeds[3]['organizations']['root']['name'],
            'AERES Hogeschool; HAS Hogeschool; Van Hall Larenstein'
        )
        self.assertEqual(seeds[5]['organizations']['root']['name'], 'SURFnet')

    def test_ideas_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['learning_material']["ideas"], [], "Expected deleted material to return no idea data")
        possible_ideas = [
            "Informatievaardigheid vocabulaire 2020",
            "Publiceren en communiceren",
            "Publiceren (van eindproduct)"
        ]
        self.assertTrue(seeds[1]['learning_material']["ideas"])
        for idea in seeds[1]['learning_material']["ideas"]:
            self.assertIn(idea, possible_ideas, "Expected material with idea elements to return the spliced strings")
        self.assertEqual(seeds[2]['learning_material']["ideas"], [], "Expected material without ideas to return empty list")
        self.assertEqual(seeds[3]['learning_material']["ideas"], [], "Expected material from other than Sharekit to ignore ideas")

    def test_study_vocabulary_property(self):
        seeds = self.seeds
        import ipdb; ipdb.set_trace()
        self.assertEqual(
            seeds[0]['learning_material']["study_vocabulary"],
            ["http://purl.edustandaard.nl/concept/8f984395-e090-41be-96df-503f53ddaa09"]
        )
        self.assertEqual(
            seeds[2]['learning_material']["study_vocabulary"], [],
            "Expected material without ideas to return empty list"
        )

    def test_lom_educational_level(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['learning_material']["lom_educational_levels"], [],
                         "Expected deleted materials to have no educational level")
        self.assertEqual(sorted(seeds[9]['learning_material']["lom_educational_levels"]), ["HBO", "HBO - Bachelor"],
                         "Expected HBO materials to have an educational level")
        self.assertEqual(sorted(seeds[2]['learning_material']["lom_educational_levels"]), ["WO", "WO - Bachelor"],
                         "Expected WO materials to have an educational level")

    def test_get_files(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["files"], [], "Expected deleted material to have no files")
        self.assertEqual(len(seeds[1]["files"]), 1)

        self.assertEqual(seeds[1]["files"],
                         ["https://surfsharekit.nl/objectstore/182216be-31a2-43c3-b7de-e5dd355b09f7"])

    def test_get_material_types(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['learning_material']["material_types"], [],
                         "Expected deleted material to have no material types")
        self.assertEqual(seeds[1]['learning_material']["material_types"], [],
                         "Expected material without a type to return empty list")
        self.assertEqual(seeds[4]['learning_material']["material_types"], ["weblecture"])

    def test_get_publisher_year(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]["publisher_year"], "Expected deleted material to have no publication year")
        self.assertIsNone(seeds[1]["publisher_year"],
                          "Expected material without publication date to have no publication year")
        self.assertEqual(seeds[3]["publisher_year"], 2017)
        self.assertEqual(seeds[8]["publisher_year"], 2020)

    def test_get_publisher_date(self):
        seeds = self.seeds
        # toDo: Add publisher date?