from django.conf import settings
from django.test import TestCase, tag

from opensearchpy import OpenSearch

from search_client.opensearch import OpenSearchClientBuilder
from search_client.constants import Entities, Platforms
from search_client.test.cases import SearchClientIntegrationTestCaseMixin


@tag("search")
class OpenSearchTestCaseMixin(SearchClientIntegrationTestCaseMixin):

    platform = None  # should be set on inheriting classes

    @classmethod
    def setup_opensearch_client(cls) -> OpenSearch:
        return OpenSearchClientBuilder.from_host(settings.OPENSEARCH_HOST).build()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Add some mock data to the indices
        cls.index_document(Entities.PRODUCTS)
        cls.index_document(
            Entities.PRODUCTS, is_last_entity_document=True,
            source="surfsharekit", external_id="abc", title=f"Nog een {Entities.PRODUCTS.value}",
            publisher_date="2020-03-18"
        )


class DocumentAPITestCase(TestCase):

    platform = None
    required_properties = {
        Platforms.EDUSOURCES: [
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
            "harvest_source",
            "has_parts",
            "is_part_of",
            "study_vocabulary",
            "doi",
            "technical_type",
            "disciplines",
        ],
        Platforms.PUBLINOVA: [
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
        for property_ in self.required_properties[self.platform]:
            self.assertIn(property_, result)
