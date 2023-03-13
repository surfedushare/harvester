from unittest.mock import patch
from datetime import datetime

from django.test import TestCase, override_settings
from django.core.management import call_command, CommandError
from django.contrib.auth.models import User
from metadata.models import MetadataField, MetadataValue


@override_settings(VERSION="0.0.1")
class TestHarvestStudyVocabulary(TestCase):
    """
    This test case represents the scenario where a harvest is started from t=0
    """

    fixtures = ["initial-study-vocabulary-resources"]
    spec_set = None
    repository = None

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="supersurf")
        self.client.force_login(self.user)

    def test_no_duplicate_error(self):
        call_command("harvest_study_vocabulary", "--vocabulary=verpleegkunde")
        call_command("harvest_study_vocabulary", "--vocabulary=verpleegkunde")

    def test_same_number_applied_science(self):
        with self.assertNumQueries(1032):
            call_command("harvest_study_vocabulary", "--vocabulary=applied-science")

    def test_data_contains_right_values(self):
        call_command("harvest_study_vocabulary", "--vocabulary=applied-science")
        value = MetadataValue.objects.get(
            value="http://purl.edustandaard.nl/concept/27aee99f-1b5f-45ba-84e9-4a52c1d46a63")
        self.assertEqual(value.name, "Python")
        self.assertEqual(value.parent.value,
                         "http://purl.edustandaard.nl/concept/982e3b48-90b9-4fbd-9365-04289afe6929")

