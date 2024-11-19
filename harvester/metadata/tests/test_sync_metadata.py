from unittest.mock import patch
from copy import copy

from django.test import TestCase, override_settings
from django.utils.timezone import now

from search_client.constants import Platforms
from metadata.models import MetadataTranslation, MetadataValue
from metadata.tasks import sync_metadata


def _translate_metadata_value_mock(field, value):
    return MetadataTranslation(nl=value, en=value, is_fuzzy=False)


@override_settings(PLATFORM=Platforms.PUBLINOVA)
@patch("metadata.tasks._translate_metadata_value", new=_translate_metadata_value_mock)
class TestSyncMetadata(TestCase):

    fixtures = ["test-metadata"]
    fetch_value_frequencies_target = "metadata.models.field.MetadataFieldManager.fetch_value_frequencies"

    def assert_metadata_value(self, field, value, frequency, is_update=True, is_deleted=False, is_insert=False,
                              parent=None, entity="products"):
        value_instance = MetadataValue.objects.get(field__name=field, field__entity__startswith=entity, value=value)
        self.assertEqual(value_instance.frequency, frequency)
        if not is_deleted:
            self.assertIsNone(value_instance.deleted_at)
        else:
            self.assertIsNotNone(value_instance.deleted_at)
        if is_update or is_insert or is_deleted:
            self.assertGreater(value_instance.updated_at, self.test_time)
        else:
            self.assertLess(value_instance.updated_at, self.test_time)
        self.assertEqual(value_instance.parent, parent)
        return value_instance

    @classmethod
    def setUpTestData(cls):
        cls.test_time = now()
        cls.test_frequencies = {
            "products:multilingual-indices--technical_type": {
                "document": 3,
                "video": 2,
                "website": 0,
                "pdf": 1
            },
            "products:default--lom_educational_levels": {
                "WO": 2,
                "HBO": 3
            },
            "products:default--harvest_source": {
                "wikiwijsmaken": 2
            },
            "projects:default--harvest_source": {
                "wikiwijsmaken": 3
            }
        }

    def test_sync_metadata(self):
        with patch(self.fetch_value_frequencies_target, return_value=self.test_frequencies):
            sync_metadata()
        # Check basic updates
        document = self.assert_metadata_value("technical_type", "document", 3)
        video = self.assert_metadata_value("technical_type", "video", 2)
        self.assert_metadata_value("lom_educational_levels", "WO", 2)
        self.assert_metadata_value("lom_educational_levels", "HBO", 3)
        self.assert_metadata_value("harvest_source", "wikiwijsmaken", 2)
        self.assert_metadata_value("harvest_source", "wikiwijsmaken", 3, entity="projects")
        # Check cross field value remain the same
        self.assert_metadata_value(
            "material_types", "document",
            frequency=300,
            is_update=False
        )
        # Check deletes
        self.assert_metadata_value(
            "technical_type", "website",
            frequency=0,
            is_deleted=True
        )
        # Check additions
        pdf = self.assert_metadata_value(
            "technical_type", "pdf",
            frequency=1,
            is_insert=True
        )
        # Everything not included in frequencies gets deleted
        upsert_ids = [document.id, video.id, pdf.id]
        for value in MetadataValue.objects.filter(field__name="technical_type").exclude(id__in=upsert_ids):
            self.assertEqual(value.frequency, 0)
            self.assertGreater(value.deleted_at, self.test_time)

    def test_sync_metadata_nested(self):
        frequencies = copy(self.test_frequencies)
        frequencies["products:default--harvest_source"] = {
            "edusources": 3,
            "wikiwijsmaken": 0,
            "MIT": 1
        }
        with patch(self.fetch_value_frequencies_target, return_value=frequencies):
            sync_metadata()

        # Check basic updates
        sharekit = self.assert_metadata_value("harvest_source", "sharekit", 0)
        self.assert_metadata_value("harvest_source", "edusources", 3, parent=sharekit)
        self.assert_metadata_value("harvest_source", "wikiwijsmaken", 3, entity="projects")
        # Check deletes
        self.assert_metadata_value("harvest_source", "wikiwijsmaken", frequency=0, is_deleted=True)
        # Check inserts
        self.assert_metadata_value("harvest_source", "MIT", frequency=1, is_insert=True)

    def test_sync_metadata_restore_deleted(self):
        for value in MetadataValue.objects.filter(value__in=["edusources", "document"]):
            value.delete()
        frequencies = copy(self.test_frequencies)
        frequencies.pop("products:multilingual-indices--technical_type")
        frequencies["products:default--harvest_source"] = {
            "edusources": 3
        }
        with patch(self.fetch_value_frequencies_target, return_value=frequencies):
            sync_metadata()
        for document in MetadataValue.objects.filter(value="document"):
            self.assertIsNotNone(document.deleted_at)
        for edusources in MetadataValue.objects.filter(value="edusources"):
            self.assertIsNone(edusources.deleted_at)
