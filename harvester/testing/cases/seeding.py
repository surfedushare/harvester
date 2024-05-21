from django.test import TestCase
from django.utils.timezone import now

from datagrowth.configuration import register_defaults
from datagrowth.resources.base import Resource

from core.models.datatypes import HarvestDocument
from core.constants import DeletePolicies
from core.loading import load_harvest_models, load_source_configuration
from core.processors import HttpSeedingProcessor
from sources.factories.protocol import ResourceFactoryProtocol


class SourceSeedingTestCase(TestCase):

    entity: str = None
    source: str = None
    resource: Resource = None
    resource_factory: ResourceFactoryProtocol = None
    delete_policy: DeletePolicies = None

    models: dict = None
    configuration: dict = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        register_defaults("global", {
            "cache_only": True
        })

    @classmethod
    def tearDownClass(cls) -> None:
        register_defaults("global", {
            "cache_only": False
        })
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.models = load_harvest_models(cls.entity)
        cls.configuration = load_source_configuration(cls.entity, cls.source)

    def setUp(self) -> None:
        super().setUp()
        # Creating test Resources
        self.resource_factory.create_common_responses()
        # Creating objects for seeding
        self.set = self.models["Set"].objects.create(name=self.source, identifier="srn")
        self.processor = HttpSeedingProcessor(self.set, {
            "phases": self.configuration["seeding_phases"]
        })

    def setup_initial_documents(self) -> list[HarvestDocument]:
        # Load the initial data, set all tasks as completed and mark everything as deleted (delete_policy=no)
        current_time = now()
        initial_documents = []
        for batch in self.processor(self.source, "1970-01-01T00:00:00Z"):
            for doc in batch:
                for task in doc.tasks.keys():
                    doc.pipeline[task] = {"success": True}
                if self.delete_policy == DeletePolicies.NO:
                    doc.properties["state"] = self.models["Document"].States.DELETED
                doc.clean()
                doc.finish_processing(current_time=current_time)
                initial_documents.append(doc)
        return initial_documents

    def setup_delta_resources(self) -> None:
        self.resource.objects.all().delete()
        self.resource_factory.create_delta_responses()

    def test_initial_seeding(self) -> list[HarvestDocument]:
        # Creating Resource test data
        self.resource_factory.create_common_responses()
        # Perform tests
        documents = []
        for batch in self.processor(self.source, "1970-01-01T00:00:00Z"):
            self.assertIsInstance(batch, list)
            for doc in batch:
                self.assertIsInstance(doc, self.models["Document"])
                self.assertIsNotNone(doc.identity)
                self.assertTrue(doc.properties)
                self.assertTrue(doc.pending_at)
                documents.append(doc)
        return documents

    def test_delta_seeding(self, become_processing_ids) -> list[HarvestDocument]:
        # Creating the test data
        self.setup_initial_documents()
        self.setup_delta_resources()
        # Test updating the initial data
        documents = []
        for batch in self.processor(self.source, "2020-01-01T00:00:00Z"):
            self.assertIsInstance(batch, list)
            for doc in batch:
                self.assertIsInstance(doc, self.models["Document"])
                self.assertIsNotNone(doc.identity)
                self.assertTrue(doc.properties)
                if doc.identity in become_processing_ids:
                    self.assertTrue(doc.pending_at)
                    self.assertIsNone(doc.finished_at)
                else:
                    self.assertIsNone(
                        doc.pending_at,
                        f"Did not expect document with identity '{doc.identity}' to be pending"
                    )
                    self.assertTrue(doc.finished_at)
                documents.append(doc)
        return documents