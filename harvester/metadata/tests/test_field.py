from unittest.mock import patch, MagicMock

from django.test import TestCase

from metadata.models import MetadataField


search_client_mock = MagicMock()
search_client_mock.search = MagicMock(return_value={
    "aggregations": {
        "field1": {
            "buckets": [
                {
                    "key": "value1",
                    "doc_count": 1
                },
                {
                    "key": "value2",
                    "doc_count": 2
                },
                {
                    "key": "value3",
                    "doc_count": 3
                }
            ]
        }
    }
})


class TestMetadataFieldManager(TestCase):

    fixtures = ["initial-metadata-edusources"]

    @patch("search.clients.get_opensearch_client", return_value=search_client_mock)
    def test_fetch_value_frequencies(self, client_mock):

        # Actual test
        frequencies = MetadataField.objects.fetch_value_frequencies()
        # Check dummy return values
        self.assertEqual(client_mock.call_count, 2, "Expected a client initialization per entity type")
        self.assertEqual(frequencies, {"field1": {"value1": 1, "value2": 2, "value3": 3}})
        # See if calls to OpenSearch were made correctly
        # First the default products call
        products_args, products_kwargs = search_client_mock.search.call_args_list[0]
        self.assertEqual(
            products_kwargs["index"], ["edusources-products"],
            "Expected 'products' entity to result in 'products:default' configuration preset"
        )
        fields = products_kwargs["body"]["aggs"]
        for field in MetadataField.objects.filter(entity__in=["products:default", "products"]):
            self.assertIn(field.name, fields)
            self.assertEqual(fields[field.name]["terms"]["size"], field.metadatavalue_set.count() + 500)
        # Now the multilingual indices products call
        multilingual_indices_args, multilingual_indices_kwargs = search_client_mock.search.call_args_list[1]
        self.assertEqual(
            multilingual_indices_kwargs["index"], ["edusources-nl", "edusources-en", "edusources-unk"],
            "Expected 'multilingual-indices' entity to use language specific indices."
        )
        fields = multilingual_indices_kwargs["body"]["aggs"]
        for field in MetadataField.objects.filter(entity="products:multilingual:indices"):
            self.assertIn(field.name, fields)
            self.assertEqual(fields[field.name]["terms"]["size"], field.metadatavalue_set.count() + 500)
