from django.test import TestCase

from django.contrib.auth.models import User

from metadata.models import MetadataField, MetadataValue


class TestMetadataFieldValuesView(TestCase):

    fixtures = ["test-metadata-edusources"]
    field = "publisher_year_normalized"

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="supersurf")
        self.client.force_login(self.user)
        self.field_instance = MetadataField.objects.get(name=self.field)
        self.field_values_queryset = MetadataValue.objects.filter(field__name=self.field)

    def assert_metadata_node_structure(self, node):
        expected_keys = {
            "value", "frequency", "field", "translation", "id", "parent", "children", "is_hidden", "is_manual",
            "children_count",
        }
        self.assertEqual(set(node.keys()), expected_keys, f"Mismatching keys for node {node['value']}")

    def assert_response_structure(self, response):
        expected_keys = {"count", "next", "previous", "results"}
        data = response.json()
        self.assertEqual(set(data.keys()), expected_keys, "Mismatching response keys")
        return data

    def test_metadata_field_values(self):
        response = self.client.get(f"/api/v1/metadata/field-values/{self.field}/")
        data = self.assert_response_structure(response)
        self.assertEqual(data["count"], self.field_values_queryset.count())
        for value in data["results"]:
            self.assert_metadata_node_structure(value)

    def test_metadata_field_values_startswith(self):
        response = self.client.get(f"/api/v1/metadata/field-values/{self.field}/20/")
        data = self.assert_response_structure(response)
        self.assertEqual(data["count"], 4)
        for value in data["results"]:
            self.assert_metadata_node_structure(value)

    def test_metadata_field_values_view_deletes(self):
        value = MetadataValue.objects.get(field__name=self.field, value="2024")
        value.delete()
        self.assertIsNotNone(value.deleted_at)
        response = self.client.get(f"/api/v1/metadata/field-values/{self.field}/")
        data = self.assert_response_structure(response)
        self.assertEqual(data["count"], self.field_values_queryset.count() - 1)
        for value in data["results"]:
            self.assert_metadata_node_structure(value)

    def test_metadata_field_values_frequency_order(self):
        # Setup manual order for disciplines
        learning_material_disciplines = MetadataField.objects.get(name="publisher_year_normalized")
        learning_material_disciplines.value_output_order = learning_material_disciplines.ValueOutputOrders.FREQUENCY
        learning_material_disciplines.save()
        # Check API output order
        response = self.client.get(f"/api/v1/metadata/field-values/{self.field}/")
        data = self.assert_response_structure(response)
        self.assertEqual([value["value"] for value in data["results"]], [
            "older-than", "2022", "2021", "2023", "2024"
        ])

    def test_metadata_field_values_manual_order(self):
        # Order for publisher_year normalized is expected to be frequency, so no changes required
        # Check API output order
        response = self.client.get(f"/api/v1/metadata/field-values/{self.field}/")
        data = self.assert_response_structure(response)
        self.assertEqual([value["value"] for value in data["results"]], [
            "2024", "2023", "2022", "2021", "older-than"
        ])

    def test_metadata_field_values_alphabetical_order(self):
        # Setup manual order for disciplines
        learning_material_disciplines = MetadataField.objects.get(name="publisher_year_normalized")
        learning_material_disciplines.value_output_order = learning_material_disciplines.ValueOutputOrders.ALPHABETICAL
        learning_material_disciplines.save()
        # Check API output order
        response = self.client.get(f"/api/v1/metadata/field-values/{self.field}/")
        data = self.assert_response_structure(response)
        self.assertEqual([value["value"] for value in data["results"]], [
            "2021", "2022", "2023", "2024", "older-than"
        ])
