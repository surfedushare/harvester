from typing import Type
import os
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.utils.timezone import now

from datagrowth.configuration import register_defaults
from datagrowth.resources.base import Resource
from datagrowth.resources.testing import ResourceFixturesMixin

from core.models.datatypes import HarvestDocument
from core.constants import DeletePolicies
from core.loading import load_harvest_models, load_source_configuration
from core.processors import HttpSeedingProcessor
from sources.factories.protocol import ResourceFactoryProtocol


class SeedingTestCase(TestCase):
    """
    Common data setup methods and common test methods for seeding processes.
    """

    entity: str = None
    source: str = None
    delete_policy: DeletePolicies = None

    storages: dict = None
    configuration: dict = None

    @classmethod
    def setUpTestData(cls) -> None:
        cls.storages = load_harvest_models(cls.entity)
        cls.configuration = load_source_configuration(cls.entity, cls.source)

    def setUp(self) -> None:
        super().setUp()
        # Creating objects for seeding
        self.set = self.storages.Set.objects.create(name=self.source, identifier="srn")
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
                    doc.task_results[task] = {"success": True}
                if self.delete_policy == DeletePolicies.NO:
                    doc.properties["state"] = self.storages.Document.States.DELETED
                doc.clean()
                doc.finish_processing(current_time=current_time)
                initial_documents.append(doc)
        return initial_documents

    def setup_delta_resources(self) -> None:
        return None

    def test_initial_seeding(self) -> list[HarvestDocument]:
        documents = []
        for batch in self.processor(self.source, "1970-01-01T00:00:00Z"):
            self.assertIsInstance(batch, list)
            for doc in batch:
                self.assertIsInstance(doc, self.storages.Document)
                self.assertIsNotNone(doc.identity)
                self.assertTrue(doc.properties)
                if doc.state == doc.States.ACTIVE:
                    self.assertTrue(doc.pending_at)
                    self.assertIsNone(doc.finished_at)
                else:
                    self.assertIsNone(doc.pending_at)
                    self.assertTrue(doc.finished_at)
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
                self.assertIsInstance(doc, self.storages.Document)
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


class FactorySeedingTestCase(SeedingTestCase):
    """
    Uses factories from the sources Django app to generate test responses during seeding
    """

    resource: Resource = None
    resource_factory: ResourceFactoryProtocol = None
    has_pagination: bool = True

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

    def setUp(self) -> None:
        # Creating test Resources through a factory
        self.resource_factory.create_common_responses()
        super().setUp()

    def check_response_fixtures(self, response_type: str) -> None:
        response_format = self.resource_factory.head["content-type"].split("/")[1]
        page_count = 1 if response_type == "delta" or not self.has_pagination else 2
        for page_number in range(0, page_count):
            response_file = f"fixture.{self.source}.{response_type}.{page_number}.{response_format}"
            response_file_path = os.path.join(settings.BASE_DIR, "sources", "factories", "fixtures", response_file)
            if not os.path.exists(response_file_path):
                raise AssertionError(f"Expected fixture {response_file_path} to run {self.__class__.__name__}")

    def setup_delta_resources(self) -> None:
        self.resource.objects.all().delete()
        self.resource_factory.create_delta_responses()

    def test_initial_seeding(self) -> list[HarvestDocument]:
        self.check_response_fixtures("initial")
        return super().test_initial_seeding()

    def test_delta_seeding(self, become_processing_ids) -> list[HarvestDocument]:
        self.check_response_fixtures("delta")
        return super().test_delta_seeding(become_processing_ids)


class ResourceFixturesSeedingTestCase(ResourceFixturesMixin, SeedingTestCase):
    """
    Uses the ResourceFixtureMixin to generate test responses during seeding.
    """
    fixtures_directory: Path
    delta_fixtures: dict[
        tuple[Type[Resource], int]: tuple[str, str]
    ]

    def setup_delta_resources(self) -> None:
        for resource_info, fixture_info in self.delta_fixtures.items():
            Resource, resource_id = resource_info
            resource = Resource.objects.get(id=resource_id)
            attr, value = fixture_info
            setattr(resource, attr, value)
            self.read_resource_attribute_fixture(str(self.fixtures_directory), resource, attr)
            resource.save()
