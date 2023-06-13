from django.conf import settings
from django.test import TestCase
from opensearchpy import OpenSearch

from search_client import SearchClient
from search_client.constants import LANGUAGES, DocumentTypes
from search_client.opensearch.configuration import create_open_search_index_configuration
from search_client.factories import generate_nl_material, generate_nl_product


class OpenSearchTestCaseMixin(object):

    search = None
    instance = None
    document_type = None
    alias_prefix = "test"

    @classmethod
    def index_body(cls, language):
        return create_open_search_index_configuration(language, DocumentTypes.LEARNING_MATERIAL)

    @classmethod
    def index_document(cls, document_type, is_last_document=False, **kwargs):
        match document_type:
            case DocumentTypes.LEARNING_MATERIAL:
                generate_document = generate_nl_material
            case DocumentTypes.RESEARCH_PRODUCT:
                generate_document = generate_nl_product
            case _:
                raise ValueError(f"Invalid document type to index_document: {document_type}")
        index_kwargs = {
            "index": cls.get_alias("nl"),
            "body": generate_document(**kwargs)
        }
        if "external_id" in kwargs:
            index_kwargs["id"] = kwargs["external_id"]
        if is_last_document:
            index_kwargs["refresh"] = True
        cls.search.index(**index_kwargs)

    @classmethod
    def get_alias(cls, language):
        return f"{cls.alias_prefix}-{language}"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Setup indices
        cls.search = OpenSearch(
            [settings.OPENSEARCH_HOST]
        )
        for language in LANGUAGES:
            cls.search.indices.create(
                cls.get_alias(language),
                ignore=400,
                body=cls.index_body('nl')
            )
        # Add some mock data to the indices
        cls.index_document(cls.document_type)
        cls.index_document(
            cls.document_type, is_last_document=True,
            external_id="abc", title=f"Nog een {cls.document_type}"
        )
        # Create a SURF SearchClient
        cls.instance = SearchClient(settings.OPENSEARCH_HOST, cls.document_type, cls.alias_prefix)

    @classmethod
    def tearDownClass(cls):
        for language in LANGUAGES:
            cls.search.indices.delete(
                cls.get_alias(language)
            )
        cls.search.close()
        cls.instance.client.close()
        super().tearDownClass()


class DocumentAPITestCase(TestCase):

    document_type = None
    required_properties = {
        DocumentTypes.LEARNING_MATERIAL: [
            "title",
            "url",
            "files",
            "description",
            "language",
            "external_id",
            "copyright",
            "lom_educational_levels",
            "published_at",
            "keywords",
            "authors",
            "publishers",
            "studies",
            "harvest_source",
            "has_parts",
            "is_part_of",
            "study_vocabulary",
            "ideas",
            "doi",
            "technical_type",
            "disciplines",
        ],
        DocumentTypes.RESEARCH_PRODUCT: [
            "title",
            "url",
            "files",
            "description",
            "language",
            "external_id",
            "copyright",
            "published_at",
            "keywords",
            "authors",
            "parties",
            "harvest_source",
            "has_parts",
            "is_part_of",
            "doi",
            "type",
            "research_themes",
            "provider",
            "owners",
            "contacts",
        ]
    }

    def assert_result_properties(self, result):
        for property_ in self.required_properties[self.document_type]:
            self.assertIn(property_, result)
