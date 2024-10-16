from unittest.mock import patch

from django.test import TestCase
from django.core.management import call_command

from datagrowth.configuration import register_defaults
from datagrowth.resources.testing import ResourceFixturesMixin
from metadata.models import MetadataValue


class TestHarvestSkosSources(ResourceFixturesMixin, TestCase):

    fixtures = ["initial-metadata-edusources", "initial-skos-sources-edusources"]
    resource_fixtures = ["skos-vocabulary-resources"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        register_defaults("global", {
            "cache_only": True
        })

    @classmethod
    def tearDownClass(cls):
        register_defaults("global", {
            "cache_only": False
        })
        super().tearDownClass()

    @patch("metadata.management.commands.harvest_skos_sources.translate_with_deepl", return_value="Translated")
    def test_no_duplicates(self, fake_deepl):
        call_command("harvest_skos_sources", "--source=Informatievaardigheid")
        call_command("harvest_skos_sources", "--source=Informatievaardigheid")
        total_objects = MetadataValue.objects.count()
        self.assertEqual(total_objects, 37,
                         "When the command runs twice it should not duplicate values.")

    @patch("metadata.management.commands.harvest_skos_sources.translate_with_deepl", return_value="Translated")
    def test_same_number_applied_science(self, fake_deepl):
        with self.assertNumQueries(165):
            call_command("harvest_skos_sources", "--source=Informatievaardigheid")

    @patch("metadata.management.commands.harvest_skos_sources.translate_with_deepl", return_value="Translated")
    def test_data_contains_right_values(self, fake_deepl):
        call_command("harvest_skos_sources", "--source=Informatievaardigheid")
        value = MetadataValue.objects.get(
            value="http://purl.edustandaard.nl/concept/598b9817-a153-400e-8710-78acadf70cbe")
        self.assertEqual(value.name, "Plannen en zoeken")
        self.assertEqual(value.parent.value, "informatievaardigheid")
        self.assertEqual(
            sorted([descendant.name for descendant in value.get_descendants()]),
            [

                "Selecteren informatiebronnen en zoeksystemen",
                "Selecteren zoektermen",
                "Zoeken naar informatie",
            ]
        )
        self.assertTrue(value.is_manual, "Expected values to be manual to prevent automatic deletion")
        self.assertEqual(
            value.field.name, "study_vocabulary.keyword",
            "Expected field to be a keyword Open Search field"
        )
        self.assertTrue(value.translation.nl)
        self.assertTrue(value.translation.en)
        self.assertTrue(value.translation.is_fuzzy)
        self.assertEqual(fake_deepl.call_count, 32)
