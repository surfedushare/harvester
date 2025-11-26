from django.test import TestCase

from projects.sources.fontys import FontysProjectExtractProcessor


class TestFontysProjectExtraction(TestCase):
    """
    Tests for Fontys project extraction logic.
    Note: Full integration tests require factory fixtures.
    """

    def test_provider(self):
        """Test that provider information is correctly configured"""
        provider = FontysProjectExtractProcessor.get_provider(None)
        self.assertEqual(provider["name"], "Fontys Hogescholen")
        self.assertEqual(provider["slug"], "fontys")

    def test_get_status(self):
        """Test project status extraction"""
        node = {"status": {"key": "FINISHED"}}
        status = FontysProjectExtractProcessor.get_status(node)
        self.assertEqual(status, "finished")

    def test_get_title(self):
        """Test title extraction"""
        node = {"title": {"nl_NL": "Test Project", "en_GB": "Test Project"}}
        title = FontysProjectExtractProcessor.get_title(node)
        self.assertEqual(title, "Test Project")

    def test_get_persons(self):
        """Test persons extraction from participants"""
        node = {
            "participants": [
                {
                    "name": {"firstName": "Alex", "lastName": "Johnson"},
                    "person": {"uuid": "test-uuid-123"}
                }
            ]
        }
        persons = FontysProjectExtractProcessor.get_persons(node)
        self.assertEqual(len(persons), 1)
        self.assertEqual(persons[0]["name"], "Alex Johnson")
        self.assertEqual(persons[0]["external_id"], "test-uuid-123")
