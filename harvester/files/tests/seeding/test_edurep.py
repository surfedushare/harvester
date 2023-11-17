from django.test import TestCase

from core.processors import HttpSeedingProcessor
from sources.factories.edurep.extraction import EdurepOAIPMHFactory
from files.models import Set as FileSet, FileDocument
from files.sources.edurep import SEEDING_PHASES


class TestEdurepFileSeeding(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        EdurepOAIPMHFactory.create_common_responses()

    def setUp(self) -> None:
        super().setUp()
        self.set = FileSet.objects.create(name="edurep", identifier="srn")
        import ipdb; ipdb.set_trace()
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })

    def test_initial_seeding(self):
        for batch in self.processor("edurep", "1970-01-01T00:00:00Z"):
            self.assertIsInstance(batch, list)
            for file_ in batch:
                self.assertIsInstance(file_, FileDocument)
                self.assertIsNotNone(file_.identity)
                self.assertTrue(file_.properties)
                self.assertTrue(file_.pending_at)
        self.assertEqual(self.set.documents.count(), 12)


class TestEdurepFileExtraction(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        EdurepOAIPMHFactory.create_common_responses()

    def setUp(self) -> None:
        super().setUp()
        self.set = FileSet.objects.create(name="edurep", identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": SEEDING_PHASES
        })
        self.seeds = []
        for batch in self.processor("edurep", "1970-01-01T00:00:00Z"):
            self.seeds += [doc.properties for doc in batch]

    def test_get_hash(self):
        import ipdb; ipdb.set_trace()
        self.assertEqual(self.seeds[0]["hash"], "0ed38cdc914e5e8a6aa1248438a1e2032a14b0de")

    def test_get_external_id(self):
        self.assertEqual(self.seeds[0]["external_id"], "0ed38cdc914e5e8a6aa1248438a1e2032a14b0de")
