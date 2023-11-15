from django.test import TestCase

from core.models import Document as CoreDocument
from products.models import ProductDocument


class TestProductDocumentCompatability(TestCase):

    backward_compatible_fields = [
        "doi", "state", "title", "authors", "keywords", "provider", "copyright", "has_parts", "is_part_of",
        "publishers", "description", "external_id", "organizations", "publisher_date", "publisher_year",
        "copyright_description", "harvest_source", "url", "mime_type", "technical_type", "ideas", "consortium",
        "material_types", "aggregation_level", "lom_educational_levels", "learning_material_disciplines",
        "research_themes", "research_object_type", "text", "suggest_phrase", "suggest_completion", "language", "video",
        "previews",
        "learning_material_disciplines_normalized",  # this is used as output for "disciplines" which itself is ignored
    ]
    removed_fields = [
        "extension",  # replaced by overwrite, currently not in use
        "parties",  # output of parties is equal to "publishers" and parties gets ignored
        "analysis_allowed", "is_restricted", "from_youtube",  # none exposed deprecated flow control fields
        "seed_resource"  # legacy debug field
    ]
    file_dependant_fields = ["url", "mime_type", "technical_type", "text", "previews"]

    fixtures = ["test-backward-compatability"]
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.core_document = CoreDocument.objects.get(id=1)
        self.product_document = ProductDocument.objects.get(id=1)

    def test_to_search(self):
        core_search = list(self.core_document.to_search())[0]  # legacy Document doesn't provide an easier way
        product_search = self.product_document.to_data(for_search=True)
        # First we check all the fields that should remain equal between core's Document and ProductDocument
        for field in self.backward_compatible_fields:
            self.assertIn(field, core_search, f"Core Document is missing search field: {field}")
            self.assertIn(field, product_search, f"ProductDocument is missing search field: {field}")
            self.assertEqual(core_search[field], product_search[field],
                             f"Search field '{field}' differs for core and product documents")
        self.assertEqual(len(core_search["files"]), len(product_search["files"]),
                         "Core Document and ProductDocument should have the same number of files")
        # Then we check if file objects on ProductDocument have at least core's file object keys and values
        # ProductDocument will expose more data in its file object, but that's irrelevant for compatibility
        for core_file, product_file in zip(core_search["files"], product_search["files"]):
            for file_field in core_file.keys():
                self.assertEqual(core_file[file_field], product_file[file_field],
                                 f"File field '{file_field}' differs for core and product files")
        # Then we check if deprecated fields in core's Document no longer exist in ProductDocument
        for field in self.removed_fields:
            self.assertNotIn(field, product_search)

    def test_to_search_no_files(self):
        # We're removing files data and fields of core Document that only get set when files are known during harvest
        self.core_document.properties["files"] = []
        self.product_document.properties["files"] = []
        for field in self.file_dependant_fields:
            self.core_document.properties[field] = None

        core_search = list(self.core_document.to_search())[0]  # legacy Document doesn't provide an easier way
        product_search = self.product_document.to_data(for_search=True)

        # We make sure that any "file" fields on core Document have the same default as ProductDocument
        for field in self.backward_compatible_fields:
            self.assertIn(field, core_search, f"Core Document is missing search field: {field}")
            self.assertIn(field, product_search, f"ProductDocument is missing search field: {field}")
            self.assertEqual(core_search[field], product_search[field],
                             f"Search field '{field}' differs for core and product documents")
        # No files should exist in the output
        self.assertEqual(len(core_search["files"]), 0)
        self.assertEqual(len(product_search["files"]), 0)
