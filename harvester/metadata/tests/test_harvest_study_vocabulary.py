from unittest.mock import patch

from django.test import TestCase, tag
from django.core.management import call_command

from datagrowth.configuration import register_defaults
from metadata.models import MetadataValue


@tag("slow")
class TestHarvestStudyVocabulary(TestCase):

    fixtures = ["initial-study-vocabulary-resources"]

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

    @patch("metadata.management.commands.harvest_study_vocabulary.translate_with_deepl", return_value="Translated")
    def test_no_duplicates(self, fake_deepl):
        call_command("harvest_study_vocabulary", "--vocabulary=verpleegkunde")
        call_command("harvest_study_vocabulary", "--vocabulary=verpleegkunde")
        total_objects = MetadataValue.objects.count()
        self.assertEqual(total_objects, 390,
                         "When the command runs twice it should not duplicate values.")

    @patch("metadata.management.commands.harvest_study_vocabulary.translate_with_deepl", return_value="Translated")
    def test_same_number_applied_science(self, fake_deepl):
        with self.assertNumQueries(879):
            call_command("harvest_study_vocabulary", "--vocabulary=applied-science")

    @patch("metadata.management.commands.harvest_study_vocabulary.translate_with_deepl", return_value="Translated")
    def test_data_contains_right_values(self, fake_deepl):
        call_command("harvest_study_vocabulary", "--vocabulary=applied-science")
        value = MetadataValue.objects.get(
            value="http://purl.edustandaard.nl/concept/27aee99f-1b5f-45ba-84e9-4a52c1d46a63")
        self.assertEqual(value.name, "Python")
        self.assertEqual(value.parent.value,
                         "http://purl.edustandaard.nl/concept/982e3b48-90b9-4fbd-9365-04289afe6929")
        self.assertEqual(
            [descendant.name for descendant in value.get_descendants()],
            [
                "NumPy", "Biopython", "Pandas", "Statistics with Python", "Python Basics",
                "Data Visualisation with Python", "Data Cleaning with Python", "Machine Learning  with Python", "SciPy"
            ]
        )
        self.assertTrue(value.is_manual, "Expected values to be manual to prevent automatic deletion")
        self.assertEqual(
            value.field.name, "study_vocabulary",
            "Expected field to be a keyword Open Search field"
        )
        self.assertTrue(value.translation.nl)
        self.assertTrue(value.translation.en)
        self.assertTrue(value.translation.is_fuzzy)
        self.assertEqual(fake_deepl.call_count, 174)
