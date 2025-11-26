from django.test import TestCase

from organizations.sources.fontys import FontysOrganizationExtraction


class TestFontysOrganizationExtraction(TestCase):
    """
    Tests for Fontys organization extraction logic.
    Note: Full integration tests require factory fixtures.
    """

    def test_provider(self):
        """Test that provider information is correctly configured"""
        provider = FontysOrganizationExtraction.get_provider(None)
        self.assertEqual(provider["name"], "Fontys Hogescholen")
        self.assertEqual(provider["slug"], "fontys")

    def test_get_name(self):
        """Test name extraction"""
        node = {"name": {"nl_NL": "Test Organisatie", "en_GB": "Test Organization"}}
        name = FontysOrganizationExtraction.get_name(node)
        self.assertEqual(name, "Test Organisatie")

    def test_parse_multilingual_value(self):
        """Test multilingual value parsing"""
        value = {"nl_NL": "Nederlands", "en_GB": "English"}
        result = FontysOrganizationExtraction.parse_multilingual_value(value)
        self.assertEqual(result, "Nederlands")

    def test_get_parents(self):
        """Test parent organization extraction"""
        node = {
            "parents": [
                {"uuid": "parent-uuid-123"}
            ]
        }
        parents = FontysOrganizationExtraction.get_parents(node)
        self.assertEqual(len(parents), 1)
        self.assertEqual(parents[0]["srn"], "fontys:organization:parent-uuid-123")
