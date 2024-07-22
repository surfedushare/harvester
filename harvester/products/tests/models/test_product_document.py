from django.test import TestCase, override_settings

from products.models import ProductDocument
from files.models import FileDocument


class FileDocumentTestCase(TestCase):

    fixtures = ["test-product-document.json"]

    def test_file_priority(self):
        # Check order when there is no priority set (default)
        product = ProductDocument.objects.get(id=1)
        product_data = product.to_data()
        file_identities = [file_["srn"] for file_ in product_data["files"]]
        self.assertEqual(file_identities, [
            "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e:7ec8985621b50d7bf29b06cf4d413191d0a20bd4",
            "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e:339df213a16895868ba4bfc635b7d3348348e33a",
            "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e:ae362bbe89cae936c89aed50dfd6b7a1cb6bf03b"
        ])
        # Set priority of link to "important" to change file order
        link_document = FileDocument.objects.filter(properties__is_link=True).first()
        link_document.properties["priority"] = 1
        link_document.save()
        product_data = product.to_data()
        file_identities = [file_["srn"] for file_ in product_data["files"]]
        self.assertEqual(file_identities, [
            "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e:ae362bbe89cae936c89aed50dfd6b7a1cb6bf03b",
            "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e:7ec8985621b50d7bf29b06cf4d413191d0a20bd4",
            "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e:339df213a16895868ba4bfc635b7d3348348e33a"
        ])

    def test_file_title_defaults(self):
        # Check title without title defaults enabled and title provided
        product = ProductDocument.objects.get(id=1)
        product_data = product.to_data()
        self.assertEqual(product_data["files"][0]["title"], "IMSCP_94812.zip")
        # Check title with title defaults enabled and title provided
        with override_settings(DEFAULT_FILE_TITLES_TEMPLATE="Attachment {ix}"):
            product_data = product.to_data()
            self.assertEqual(product_data["files"][0]["title"], "IMSCP_94812.zip")
        # Check title without title defaults enabled and title missing
        file_document = FileDocument.objects.first()
        file_document.properties["title"] = None
        file_document.save()
        product_data = product.to_data()
        self.assertIsNone(product_data["files"][0]["title"])
        # Check title with default enabled and title missing
        with override_settings(DEFAULT_FILE_TITLES_TEMPLATE="Attachment {ix}"):
            product_data = product.to_data()
            self.assertEqual(product_data["files"][0]["title"], "Attachment 1")

    @override_settings(SET_PRODUCT_COPYRIGHT_BY_MAIN_FILE_COPYRIGHT=False)
    def test_to_search_no_files(self):
        FileDocument.objects.all().delete()
        product = ProductDocument.objects.get(id=1)
        product_search = product.to_data(for_search=True)
        self.assertIsNone(product_search["url"])
        self.assertIsNone(product_search["mime_type"])
        self.assertIsNone(product_search["technical_type"])
        self.assertIsNone(product_search["text"])
        self.assertIsNone(product_search["previews"])
        self.assertEqual(product_search["files"], [])

    def test_technical_type_overrides(self):
        """
        Technical type is file dependant, but we make sure that it gets inherited from ProductDocument if required
        """
        # Test ProductDocument override
        product = ProductDocument.objects.get(id=1)
        product.properties["technical_type"] = "video"
        product_search = product.to_data(for_search=True)
        self.assertEqual(product_search["technical_type"], "video",
                         "If set on ProductDocument the technical_type should override the FileDocument.type")
        # Test override if there are no files at all
        FileDocument.objects.all().delete()
        product.properties["technical_type"] = None
        product_search = product.to_data(for_search=True)
        self.assertIsNone(product_search["technical_type"],
                          "Expected technical_type to be None if there are no files and ProductDocument doesn't set it")
        product.properties["technical_type"] = "website"
        product_search = product.to_data(for_search=True)
        self.assertEqual(product_search["technical_type"], "website",
                         "Expected ProductDocument to dictate technical_type without any files present")

    def test_copyright_overrides(self):
        """
        Copyright is file dependant, when this is enabled in settings and product doesn't provide a value.
        """
        # Remove the product copyright and see if file copyright emerges.
        product = ProductDocument.objects.get(id=1)
        product.properties["copyright"] = None
        product_search = product.to_data(for_search=True)
        self.assertEqual(product_search["copyright"], "cc-by-sa-40")
        # Test no product copyright and this feature disabled (tests use Edusources settings where this is enabled)
        with override_settings(SET_PRODUCT_COPYRIGHT_BY_MAIN_FILE_COPYRIGHT=False):
            product_search = product.to_data(for_search=True)
            self.assertIsNone(product_search["copyright"], "cc-by-nd-40")
        # Now we remove the value from FileDocument to see if the "yes" default shows up.
        file_document = FileDocument.objects.get(id=1)
        file_document.properties["copyright"] = None
        file_document.save()
        product_search = product.to_data(for_search=True)
        self.assertEqual(product_search["copyright"], "yes")
        # And finally we remove all files from product. It again should show the "yes" default.
        FileDocument.objects.all().delete()
        product_search = product.to_data(for_search=True)
        self.assertEqual(product_search["copyright"], "yes")

    def test_multilingual_indices_to_data(self):
        product = ProductDocument.objects.get(id=1)
        data = product.to_data(for_search=False)
        self.assertEqual(data["learning_material_disciplines_normalized"], [
            "exact_informatica"
        ])
        self.assertEqual(data["disciplines_normalized"], [
            "exact_informatica"
        ])
        self.assertEqual(data["publisher_year_normalized"], "older-than")
        self.assertEqual(data["study_vocabulary"], [
            "http://purl.edustandaard.nl/concept/128a7da4-7d5c-4625-8b16-fec02aa94f5d",
            "http://purl.edustandaard.nl/concept/43943d13-306a-4838-a9d4-6a3c4f7a8e11",
            "applied-science"
        ])
        self.assertEqual(data["study_vocabulary_terms"], [
            "Python",
            "Applied Science",
            "Applied Science"
        ])
        self.assertEqual(data["consortium"], "Stimuleringsregeling Open en Online Onderwijs")
