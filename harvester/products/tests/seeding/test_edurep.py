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
            for product in batch:
                self.assertIsInstance(product, ProductDocument)
                self.assertIsNotNone(product.identity)
                self.assertTrue(product.properties)
                if product.state == ProductDocument.States.ACTIVE:
                    self.assertTrue(product.pending_at)
                    self.assertIsNone(product.finished_at)
                else:
                    self.assertIsNone(product.pending_at)
                    self.assertIsNotNone(product.finished_at)
        self.assertEqual(self.set.documents.count(), 9)

    def test_delta_seeding(self):
        # Load the initial data, set all tasks as completed and create delta Resource
        initial_documents = []
        for batch in self.processor("edurep", "1970-01-01T00:00:00Z"):
            for doc in batch:
                for task in doc.tasks.keys():
                    doc.pipeline[task] = {"success": True}
                doc.finish_processing()
                initial_documents.append(doc)
        EdurepOAIPMHFactory.create(is_initial=False, number=0)
        # Set some expectations
        become_processing_ids = {
            # Changed study_vocabulary by the delta
            "edurep:surfsharekit:surfsharekit:oai:surfsharekit.nl:b5473dd1-8aa4-455f-b359-9af8081ce697",
            # Documents added by the delta
            "edurep:surfsharekit:surfsharekit:oai:surfsharekit.nl:3e45b9e3-ba76-4200-a927-2902177f1f6c",
            "edurep:surfsharekit:surfsharekit:oai:surfsharekit.nl:4842596f-fe60-40ef-8c06-4d3d6e296ba4",
        }
        # Load the delta data and see if updates have taken place
        documents = []
        for batch in self.processor("edurep", "2020-02-10T13:08:39Z"):
            self.assertIsInstance(batch, list)
            for product in batch:
                self.assertIsInstance(product, ProductDocument)
                self.assertIsNotNone(product.identity)
                self.assertTrue(product.properties)
                if product.identity in become_processing_ids:
                    self.assertTrue(product.pending_at)
                    self.assertIsNone(product.finished_at)
                else:
                    self.assertIsNone(product.pending_at)
                    self.assertTrue(product.finished_at)
                documents.append(product)
        self.assertEqual(len(documents), 2 + 2 + 2, "Expected two additions, two deletions and two updates")
        self.assertEqual(
            self.set.documents.count(), 9 + 2 + 1,
            "Expected 13 initial Documents, 2 delta additions and one delete that didn't exist before"
        )

    def test_empty_seeding(self):
        EdurepOAIPMHFactory.create(is_initial=False, number=0, is_empty=True)  # delta without results
        for batch in self.processor("edurep", "2020-02-10T13:08:39Z"):
            self.assertEqual(batch, [])
        self.assertEqual(self.set.documents.count(), 0)


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

    def test_get_external_id(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]["external_id"], "surfsharekit:oai:surfsharekit.nl:3d2940a0-9573-412e-8fa2-067c55e2a72f"
        )

    def test_get_set(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["set"], "edurep:surfsharekit")

    def test_get_modified_at(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["modified_at"], "2019-11-05T00:06:37Z")

    def test_authors_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[3]['authors'], [
            {
                "name": "Ruud Kok",
                "email": None,
                "external_id": None,
                "dai": None,
                "orcid": None,
                "isni": None,
                "is_external": None,
            }
        ])

    def test_publishers_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publishers"], [], "Expected deleted material to have no publishers")
        self.assertEqual(
            seeds[3]['publishers'], ['AERES Hogeschool; HAS Hogeschool; Van Hall Larenstein'],
            "Expected escaped semi-colons to not break VCard parsing"
        )
        self.assertEqual(seeds[4]['publishers'], ['SURFnet'])

    def test_consortium(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]['learning_material']['consortium'], None,
            "Expected deleted material to have no consortium"
        )
        self.assertEqual(
            seeds[1]['learning_material']['consortium'], 'HBO Verpleegkunde',
            "Expected HBO Verpleegkunde to be added based on keywords"
        )

    def test_organizations(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]['organizations']['root']['name'], "Edurep",
            "Expected default organization to be Edurep"
        )
        self.assertEqual(
            seeds[3]['organizations']['root']['name'],
            'AERES Hogeschool; HAS Hogeschool; Van Hall Larenstein',
            "Expected semi colons in organization VCards to be escaped properly"
        )
        self.assertEqual(seeds[4]['organizations']['root']['name'], 'SURFnet')

    def test_study_vocabulary(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]['learning_material']["study_vocabulary"], [],
            "Expected material without vocabulary terms to return empty list"
        )
        self.assertEqual(
            seeds[1]['learning_material']["study_vocabulary"],
            ["http://purl.edustandaard.nl/concept/8f984395-e090-41be-96df-503f53ddaa09"]
        )

    def test_lom_educational_level(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['learning_material']["lom_educational_levels"], [],
                         "Expected deleted materials to have no educational level")
        self.assertEqual(sorted(seeds[2]['learning_material']["lom_educational_levels"]), ["WO", "WO - Bachelor"])
        self.assertEqual(sorted(seeds[4]['learning_material']["lom_educational_levels"]), ["WO"],
                         "Expected L4L materials to be marked as WO")

    def test_get_files(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["files"], [], "Expected deleted material to have no files")
        self.assertEqual(seeds[1]["files"],
                         ["https://surfsharekit.nl/objectstore/182216be-31a2-43c3-b7de-e5dd355b09f7"])

    def test_get_material_types(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['learning_material']["material_types"], ["unknown"],
                         "Expected deleted material to have no material types")
        self.assertEqual(seeds[1]['learning_material']["material_types"], ["weblecture"])
        self.assertEqual(seeds[2]['learning_material']["material_types"], ["unknown"],
                         "Expected material without a type to return list with the default")

    def test_get_publisher_year(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]["publisher_year"], "Expected deleted material to have no publication year")
        self.assertIsNone(seeds[1]["publisher_year"],
                          "Expected material without publication date to have no publication year")
        self.assertEqual(seeds[3]["publisher_year"], 2017)
        self.assertEqual(seeds[4]["publisher_year"], 2020)

    def test_get_publisher_date(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]["publisher_date"], "Expected deleted material to have no publication year")
        self.assertIsNone(seeds[1]["publisher_date"],
                          "Expected material without publication date to have no publication year")
        self.assertEqual(seeds[3]["publisher_date"], "2017-09-27")
        self.assertEqual(seeds[4]["publisher_date"], "2020-09-21")

    def test_get_title(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]["title"], "Deleted item should be None")
        self.assertEqual(seeds[1]["title"], "Exercises 5", "Expected no newlines in the title")
        self.assertEqual(seeds[2]["title"], "Using a Vortex | Wageningen UR")

    def test_get_description(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]["description"], "Deleted item should be None")
        self.assertEqual(seeds[1]["description"], "Fifth exercises of the course")
        self.assertEqual(
            seeds[2]["description"], "Instruction on how to use a Vortex mixer",
            "Expected no newlines or carriage returns in the description"
        )

    def test_get_copyright(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["copyright"], 'yes', "Deleted item should be yes")
        self.assertEqual(
            seeds[1]["copyright"], "cc-by-nc-40",
            "Expected copyright from description if normal copyright is only 'yes'"
        )
        self.assertEqual(seeds[2]["copyright"], "cc-by-40")

    def test_get_copyright_description(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]["copyright_description"], "Deleted item should be None")
        self.assertEqual(seeds[1]["copyright_description"], 'https://creativecommons.org/licenses/by-nc/4.0/')

    def test_get_language(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]["language"], "Deleted item should be None")
        self.assertEqual(seeds[1]["language"], "en")
        self.assertEqual(seeds[3]["language"], "nl")

    def test_get_keywords(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["keywords"], [], "Deleted item should have empty list")
        self.assertEqual(seeds[1]["keywords"], ['Exercise', '#HBOVPK'])

    def test_get_aggregation_level(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]["learning_material"]["aggregation_level"], "Deleted item should have empty list")
        self.assertIsNone(
            seeds[1]["learning_material"]["aggregation_level"],
            'Expected material without aggregation level to specify None'
        )
        self.assertEqual(seeds[3]["learning_material"]["aggregation_level"], '4')

    def test_get_disciplines(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["learning_material"]["disciplines"], [], "Deleted item should have empty list")
        self.assertEqual(seeds[1]["learning_material"]["disciplines"], ["8f984395-e090-41be-96df-503f53ddaa09"])
