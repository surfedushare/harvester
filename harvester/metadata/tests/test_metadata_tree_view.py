from django.test import TestCase

from django.contrib.auth.models import User

from metadata.models import MetadataField, MetadataValue


class TestMetadataTreeView(TestCase):

    fixtures = ["test-metadata-edusources"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="supersurf")
        self.client.force_login(self.user)

    @staticmethod
    def find_field_in_response(response, field_name):
        data = response.json()
        return next(
            (field for field in data if field["value"] == field_name),
            None
        )

    def assert_metadata_node_structure(self, node):
        expected_keys = {
            "value", "frequency", "field", "translation", "id", "parent", "children", "is_hidden", "is_manual",
            "children_count",
        }
        self.assertEqual(set(node.keys()), expected_keys, node["value"])

    def test_metadata_tree_view(self):
        response = self.client.get("/api/v1/metadata/tree/")
        data = response.json()
        self.assertEqual(len(data), MetadataField.objects.filter(is_hidden=False).count())
        for field in data:
            self.assertIsNone(field["field"])
            self.assert_metadata_node_structure(field)
            for child in field["children"]:
                self.assertEqual(child["field"], field["value"])
                self.assert_metadata_node_structure(child)

    def test_metadata_tree_view_max_children(self):
        max_children = 2
        response = self.client.get(f"/api/v1/metadata/tree/?max_children={max_children}")
        data = response.json()
        self.assertEqual(len(data), MetadataField.objects.filter(is_hidden=False).count())
        for field in data:
            self.assertIsNone(field["field"])
            self.assert_metadata_node_structure(field)
            self.assertLessEqual(len(field["children"]), max_children)
            self.assert_metadata_node_structure(field)
            for child in field["children"]:
                self.assertEqual(child["field"], field["value"])
                self.assert_metadata_node_structure(child)

    def test_metadata_tree_view_deletes(self):
        document = MetadataValue.objects.get(field__name="technical_type", value="document")
        document.delete()
        self.assertIsNotNone(document.deleted_at)
        response = self.client.get("/api/v1/metadata/tree/")
        data = response.json()
        self.assertEqual(len(data), MetadataField.objects.filter(is_hidden=False).count())
        technical_type = next(field for field in data if field["value"] == "technical_type")
        for child in technical_type["children"]:
            self.assertNotEqual(child["value"], "document")
        material_types = next(field for field in data if field["value"] == "material_types")
        material_type_document = next(child for child in material_types["children"] if child["value"] == "document")
        self.assertIsNotNone(material_type_document)

    def test_metadata_tree_frequency_order(self):
        # Default order is expected to be frequency, so no changes required
        # Check API output order
        response = self.client.get("/api/v1/metadata/tree/")
        disciplines = self.find_field_in_response(response, "learning_material_disciplines_normalized")
        self.assertEqual([value["value"] for value in disciplines["children"]], [
            "gedrag_maatschappij",
            "interdisciplinair",
            "techniek",
            "aarde_milieu",
            "economie_bedrijf",
            "exact_informatica",
            "gezondheid",
            "kunst_cultuur",
            "onderwijs_opvoeding",
            "recht_bestuur",
            "taal_communicatie"
        ])

    def test_metadata_tree_manual_order(self):
        # Setup manual order for disciplines
        learning_material_disciplines = MetadataField.objects.get(name="learning_material_disciplines_normalized")
        learning_material_disciplines.value_output_order = learning_material_disciplines.ValueOutputOrders.MANUAL
        learning_material_disciplines.save()
        # Check API output order
        response = self.client.get("/api/v1/metadata/tree/")
        disciplines = self.find_field_in_response(response, "learning_material_disciplines_normalized")
        self.assertEqual([value["value"] for value in disciplines["children"]], [
            "techniek",
            "aarde_milieu",
            "economie_bedrijf",
            "exact_informatica",
            "gedrag_maatschappij",
            "gezondheid",
            "interdisciplinair",
            "kunst_cultuur",
            "onderwijs_opvoeding",
            "recht_bestuur",
            "taal_communicatie"
        ])

    def test_metadata_tree_alphabetical_order(self):
        # Setup manual order for disciplines
        learning_material_disciplines = MetadataField.objects.get(name="learning_material_disciplines_normalized")
        learning_material_disciplines.value_output_order = learning_material_disciplines.ValueOutputOrders.ALPHABETICAL
        learning_material_disciplines.save()
        # Check API output order
        response = self.client.get("/api/v1/metadata/tree/")
        disciplines = self.find_field_in_response(response, "learning_material_disciplines_normalized")
        self.assertEqual([value["value"] for value in disciplines["children"]], [
            "aarde_milieu",
            "economie_bedrijf",
            "exact_informatica",
            "gedrag_maatschappij",
            "gezondheid",
            "interdisciplinair",
            "kunst_cultuur",
            "onderwijs_opvoeding",
            "recht_bestuur",
            "taal_communicatie",
            "techniek"
        ])
