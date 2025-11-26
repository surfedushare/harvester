from django.test import TestCase

from persons.sources.fontys import FontysPersonsExtractProcessor


class TestFontysPersonExtraction(TestCase):
    """
    Tests for Fontys person extraction logic.
    Note: Full integration tests require factory fixtures.
    """

    def test_provider(self):
        """Test that provider information is correctly configured"""
        provider = FontysPersonsExtractProcessor.get_provider(None)
        self.assertEqual(provider["name"], "Fontys Hogescholen")
        self.assertEqual(provider["slug"], "fontys")

    def test_get_name(self):
        """Test name extraction from node"""
        node = {"name": {"firstName": "Alex", "lastName": "Johnson"}}
        name = FontysPersonsExtractProcessor.get_name(node)
        self.assertEqual(name, "Alex Johnson")

    def test_get_name_with_missing_firstname(self):
        """Test name extraction when firstName is missing"""
        node = {"name": {"lastName": "Johnson"}}
        name = FontysPersonsExtractProcessor.get_name(node)
        self.assertEqual(name, "Johnson")

    def test_get_is_employed(self):
        """Test employment status extraction"""
        node = {
            "staffOrganizationAssociations": [
                {"period": {"startDate": "2020-01-01"}}  # No end date = currently employed
            ]
        }
        is_employed = FontysPersonsExtractProcessor.get_is_employed(node)
        self.assertTrue(is_employed)
