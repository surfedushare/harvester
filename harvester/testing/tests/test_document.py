from copy import copy

from django.test import TestCase
from django.utils.timezone import now

from testing.constants import ENTITY_SEQUENCE_PROPERTIES
from testing.models import Dataset, DatasetVersion, Set, TestDocument
from testing.utils.generators import seed_generator


class TestDocumentModel(TestCase):

    def setUp(self):
        super().setUp()
        self.dataset = Dataset.objects.create(
            name="test",
            is_harvested=True,
            indexing=Dataset.IndexingOptions.INDEX_AND_PROMOTE
        )
        self.dataset_version = DatasetVersion.objects.create(dataset=self.dataset)
        self.set = Set.objects.create(
            name="simple",
            pending_at=None,  # HarvestSet does not become pending until all data from source has been pulled
            identifier="srn",
            dataset_version=self.dataset_version
        )
        self.sequence_properties = copy(ENTITY_SEQUENCE_PROPERTIES["simple"])
        seed = list(seed_generator("simple", 1, self.sequence_properties))[0]
        self.document = TestDocument.build(seed, collection=self.set)
        self.document.save()

    def test_get_property_dependencies(self):
        property_dependencies = self.document.get_property_dependencies()
        self.assertEqual(property_dependencies, {
            "$.url": ["tika"]
        })

    def test_invalidate_task(self):
        # Setup the document to reflect that pipeline tasks have run
        self.document.pipeline["tika"] = {"success": True}
        self.document.derivatives["tika"] = {"texts": ["I will disappear"]}
        self.document.pipeline["other"] = {"success": False}
        self.document.derivatives["other"] = {"texts": ["I will remain"]}
        self.document.pending_at = None
        self.document.save()
        # Invalidate the Tika task
        self.document.invalidate_task("tika")
        # Assert the document
        self.assertNotIn("tika", self.document.pipeline)
        self.assertNotIn("tika", self.document.derivatives)
        self.assertEqual(self.document.pipeline["other"], {"success": False})
        self.assertEqual(self.document.derivatives["other"], {"texts": ["I will remain"]})
        self.assertIsNotNone(
            self.document.pending_at,
            "Expected document to become pending after invalidating a task"
        )
        self.assertIsNone(
            self.document.finished_at,
            "Expected document to be unfinished after invalidating a task"
        )
        # Remove the pending state
        self.document.pending_at = None
        self.document.finished_at = now()
        self.document.save()
        # Invalidate a non existing task
        self.document.invalidate_task("does_not_exist")
        # Assert the document
        self.assertEqual(self.document.pipeline["other"], {"success": False})
        self.assertEqual(self.document.derivatives["other"], {"texts": ["I will remain"]})
        self.assertIsNone(self.document.pending_at, "Expected document to remain un-pending if task didn't exist")
        self.assertIsNotNone(
            self.document.finished_at,
            "Expected document to remain finished if task didn't exist"
        )

    def test_update_url(self):
        # Setup the document to reflect that pipeline tasks have run
        self.document.pipeline["tika"] = {"success": True}
        self.document.derivatives["tika"] = {"texts": ["I will disappear"]}
        self.document.pending_at = None
        self.document.finished_at = now()
        self.document.save()
        # Update the document
        self.document.update({"url": None})
        # Assert the document
        self.assertNotIn("tika", self.document.pipeline)
        self.assertNotIn("tika", self.document.derivatives)
        self.assertIsNotNone(self.document.pending_at, "Expected Document to become pending after updating URL")
        self.assertIsNone(self.document.finished_at, "Expected Document to not be finished after updating URL")

    def test_update_nested(self):
        self.document.update({
            "title": "main title",
            "nested.title": "nested title"
        })
        self.assertEqual(self.document.properties["title"], "main title")
        self.assertIsInstance(self.document.properties["nested"], dict, "Expected nested dict to get created")
        self.assertEqual(self.document.properties["nested"]["title"], "nested title")
