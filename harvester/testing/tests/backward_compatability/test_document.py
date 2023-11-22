from django.test import TestCase

from core.models import Document as LegacyDocument
from products.models import ProductDocument
from files.models import FileDocument


class TestProductDocumentCompatability(TestCase):

    backward_compatible_fields = [
        "doi", "state", "title", "authors", "keywords", "provider", "copyright", "has_parts", "is_part_of",
        "publishers", "description", "external_id", "organizations", "publisher_date", "publisher_year",
        "copyright_description", "harvest_source", "url", "mime_type", "technical_type", "ideas", "consortium",
        "material_types", "aggregation_level", "lom_educational_levels", "learning_material_disciplines",
        "research_themes", "research_object_type", "text", "suggest_phrase", "suggest_completion", "language", "video",
        "previews", "studies",
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
        self.legacy_document = LegacyDocument.objects.get(id=1)
        self.product_document = ProductDocument.objects.get(id=1)

    def test_to_search(self):
        legacy_search = list(self.legacy_document.to_search())[0]  # legacy Document doesn't provide an easier way
        product_search = self.product_document.to_data(for_search=True)
        # First we check all the fields that should remain equal between LegacyDocument and ProductDocument
        for field in self.backward_compatible_fields:
            self.assertIn(field, legacy_search, f"LegacyDocument is missing search field: {field}")
            self.assertIn(field, product_search, f"ProductDocument is missing search field: {field}")
            self.assertEqual(legacy_search[field], product_search[field],
                             f"Search field '{field}' differs for legacy and product documents")
        self.assertEqual(len(legacy_search["files"]), len(product_search["files"]),
                         "LegacyDocument and ProductDocument should have the same number of files")
        # Then we check if file objects on ProductDocument have at least legacy file object keys and values
        # ProductDocument will expose more data in its file object, but that's irrelevant for compatibility
        for legacy_file, product_file in zip(legacy_search["files"], product_search["files"]):
            for file_field in legacy_file.keys():
                self.assertEqual(legacy_file[file_field], product_file[file_field],
                                 f"File field '{file_field}' differs for legacy and product files")
        # Then we check if deprecated fields in LegacyDocument no longer exist in ProductDocument
        for field in self.removed_fields:
            self.assertNotIn(field, product_search)

    def test_to_search_no_files(self):
        # We're removing files data and fields of LegacyDocument that only get set when files are known during harvest
        self.legacy_document.properties["files"] = []
        self.product_document.properties["files"] = []
        for field in self.file_dependant_fields:
            self.legacy_document.properties[field] = None
        FileDocument.objects.all().delete()

        legacy_search = list(self.legacy_document.to_search())[0]  # legacy Document doesn't provide an easier way
        product_search = self.product_document.to_data(for_search=True)

        # We make sure that any "file" fields on LegacyDocument have the same default as ProductDocument
        for field in self.backward_compatible_fields:
            self.assertIn(field, legacy_search, f"LegacyDocument is missing search field: {field}")
            self.assertIn(field, product_search, f"ProductDocument is missing search field: {field}")
            self.assertEqual(legacy_search[field], product_search[field],
                             f"Search field '{field}' differs for legacy and product documents")
        # No files should exist in the output
        self.assertEqual(len(legacy_search["files"]), 0)
        self.assertEqual(len(product_search["files"]), 0)

    def test_technical_type_overrides(self):
        """
        Technical type is file dependant, but we make sure that it gets inherited from ProductDocument if required
        """
        # Test ProductDocument override
        self.product_document.properties["technical_type"] = "video"
        product_search = self.product_document.to_data(for_search=True)
        self.assertEqual(product_search["technical_type"], "video",
                         "If set on ProductDocument the technical_type should override the FileDocument.type")
        # Test override if there are no files at all
        FileDocument.objects.all().delete()
        self.product_document.properties["technical_type"] = None
        product_search = self.product_document.to_data(for_search=True)
        self.assertIsNone(product_search["technical_type"],
                          "Expected technical_type to be None if there are no files and ProductDocument doesn't set it")
        self.product_document.properties["technical_type"] = "website"
        product_search = self.product_document.to_data(for_search=True)
        self.assertEqual(product_search["technical_type"], "website",
                         "Expected ProductDocument to dictate technical_type without any files present")
