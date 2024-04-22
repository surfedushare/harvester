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
