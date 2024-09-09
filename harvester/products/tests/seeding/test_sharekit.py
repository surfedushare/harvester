from django.test import TestCase

from core.processors import HttpSeedingProcessor
from sources.factories.sharekit.extraction import SharekitMetadataHarvestFactory
from products.models import Set, ProductDocument
from products.sources.sharekit import SEEDING_PHASES


class TestSharekitProductSeeding(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        SharekitMetadataHarvestFactory.create_common_sharekit_responses()

    def setUp(self) -> None:
        super().setUp()
        self.set = Set.objects.create(name="edusources", identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })

    def test_initial_seeding(self):
        for batch in self.processor("edusources", "1970-01-01T00:00:00Z"):
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
        self.assertEqual(self.set.documents.count(), 11)

    def test_delta_seeding(self):
        # Load the initial data, set all tasks as completed and create delta Resource
        initial_documents = []
        for batch in self.processor("edusources", "1970-01-01T00:00:00Z"):
            for doc in batch:
                for task in doc.tasks.keys():
                    doc.pipeline[task] = {"success": True}
                doc.finish_processing()
                initial_documents.append(doc)
        SharekitMetadataHarvestFactory.create(is_initial=False, number=0)
        # Set some expectations
        become_processing_ids = {
            "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e",  # Changed study_vocabulary by the delta
            # Documents added by the delta
            "sharekit:edusources:3e45b9e3-ba76-4200-a927-2902177f1f6c",
            "sharekit:edusources:4842596f-fe60-40ef-8c06-4d3d6e296ba4",
            "sharekit:edusources:f4e867ba-0bd0-489a-824a-752038dfee63",
        }
        # Load the delta data and see if updates have taken place
        documents = []
        for batch in self.processor("edusources", "2020-02-10T13:08:39Z"):
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
        self.assertEqual(len(documents), 3 + 1 + 1, "Expected two additions, one deletion and one update")
        self.assertEqual(self.set.documents.count(), 14, "Expected 11 initial Documents and 3 delta additions")

    def test_empty_seeding(self):
        SharekitMetadataHarvestFactory.create(is_initial=False, number=0, is_empty=True)  # delta without results
        for batch in self.processor("edusources", "2020-02-10T13:08:39Z"):
            self.assertEqual(batch, [])
        self.assertEqual(self.set.documents.count(), 0)


class TestSharekitProductExtraction(TestCase):

    set = None
    seeds = []

    @classmethod
    def setUpTestData(cls):
        SharekitMetadataHarvestFactory.create_common_sharekit_responses()
        cls.set = Set.objects.create(name="edusources", identifier="srn")
        processor = HttpSeedingProcessor(cls.set, {
            "phases": SEEDING_PHASES
        })
        cls.seeds = []
        for batch in processor("edusources", "1970-01-01T00:00:00Z"):
            cls.seeds += [doc.properties for doc in batch]

    def test_provider(self):
        self.assertEqual(self.seeds[0]["provider"], {
            "ror": None,
            "external_id": "33838b37-28f1-4269-b026-86f6577d53cb",
            "slug": None,
            "name": "Stimuleringsregeling Open en Online Onderwijs"
        })

    def test_modified_at(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["modified_at"], "2017-12-11T12:52:09Z")

    maxDiff = None

    def test_authors_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[2]['authors'], [
            {
                "name": "Ruudje Cock",
                "email": "Ruudje Cock",
                "external_id": "83e7c163-075e-4eb2-8247-d975cf047dba",
                "dai": None,
                "orcid": None,
                "isni": None,
                "is_external": False
            },
            {
                "name": "A. Puist",
                "email": "A. Puist",
                "external_id": "1174c1b9-f010-4a0a-98c0-2ceeefd0b506",
                "dai": None,
                "orcid": None,
                "isni": None,
                "is_external": False,
            },
            {
                "name": "Hans Kazan",
                "email": "Hans Kazan",
                "external_id": "c0ab267a-ad56-480c-a13a-90b325f45b5d",
                "dai": None,
                "orcid": None,
                "isni": None,
                "is_external": True
            },
        ])

    def test_publishers_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[2]['publishers'], ["Hogeschool Utrecht", 'SURFnet'])
        self.assertEqual(seeds[4]['publishers'], ['SURFnet'])

    def test_consortium(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['learning_material']['consortium'], 'Stimuleringsregeling Open en Online Onderwijs')
        self.assertIsNone(seeds[1]['learning_material']['consortium'])

    def test_organizations(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["organizations"]["root"]["name"], "Stimuleringsregeling Open en Online Onderwijs")

    def test_is_part_of_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['is_part_of'], [], "Expected standard material to have no parent")
        self.assertEqual(
            seeds[4]['is_part_of'],
            ["3c2b4e81-e9a1-41bc-8b6a-97bfe7e4048b"],
            "Expected child material to specify its parent"
        )

    def test_has_parts_property(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['has_parts'], [], "Expected standard material to have no parts")
        self.assertEqual(
            seeds[3]['has_parts'],
            [
                "a18cdda7-e9c7-40d7-a7ad-6e875d9015ce",
                "8936d0a3-4157-45f4-9595-c26d4c029d97",
                "f929b625-5ef7-47b8-8fa8-94c969d0c427",
                "befb515c-5dce-4f27-82a4-2f5a7a3618a4"
            ],
            "Expected parent material to have children and specify the external ids"
        )
        self.assertEqual(seeds[5]['has_parts'], [], "Expected child material to have no children")

    def test_study_vocabulary_property(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]['learning_material']["study_vocabulary"],
            ["http://purl.edustandaard.nl/concept/8f984395-e090-41be-96df-503f53ddaa09"]
        )
        self.assertEqual(
            seeds[2]['learning_material']["study_vocabulary"], [],
            "Expected material without vocabulary terms to return empty list"
        )

    def test_lom_educational_level(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]['learning_material']["lom_educational_levels"], ["HBO"],
                         "Expected HBO materials to have an educational level")
        self.assertEqual(seeds[1]['learning_material']["lom_educational_levels"], ["WO"],
                         "Expected HBO materials to have an educational level")

    def test_get_files(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["files"], [
            "https://surfsharekit.nl/objectstore/182216be-31a2-43c3-b7de-e5dd355b09f7"
        ])
        self.assertEqual(seeds[2]["files"], [
                "https://surfsharekit.nl/objectstore/88c687c8-fbc4-4d69-a27d-45d9f30d642b",
                "https://surfsharekit.nl/objectstore/9f71f782-09de-48b1-a10f-15d882471df7",
                "https://maken.wikiwijs.nl/94812/Macro_meso_micro#!page-2935729"
        ])

    def test_get_material_types(self):
        seeds = self.seeds
        self.assertEqual(
            seeds[0]['learning_material']["material_types"], ["unknown"],
            "Expected material without a type to return empty list"
        )
        self.assertEqual(
            seeds[1]['learning_material']["material_types"], ["unknown"],
            "Expected material with null as type to return empty list"
        )
        self.assertEqual(seeds[3]['learning_material']["material_types"], ["kennisoverdracht"])
        self.assertEqual(seeds[4]['learning_material']["material_types"], ["kennisoverdracht"],
                         "Expected a single value to transform to a list")
        self.assertEqual(seeds[5]['learning_material']["material_types"], ["kennisoverdracht"],
                         "Expected null values to get filtered from lists")

    def test_get_publisher_year(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_year"], 2019)
        self.assertIsNone(seeds[8]["publisher_year"], "Expected deleted material to have no publisher year")

    def test_get_publisher_date(self):
        seeds = self.seeds
        self.assertEqual(seeds[0]["publisher_date"], "2019-01-01")
        self.assertEqual(seeds[1]["publisher_date"], "2016-09-02")
        self.assertIsNone(seeds[2]["publisher_date"])

    def test_technical_type(self):
        seeds = self.seeds
        self.assertIsNone(seeds[0]["technical_type"], "Expected unknown technical types to be None for product")
        self.assertEqual(seeds[3]["technical_type"], "video", "Expected technicalFormat to be used when present")
