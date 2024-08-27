from typing import Type

from django.conf import settings
from rest_framework.serializers import Serializer
from pydantic import BaseModel
from opensearchpy import OpenSearch

from search_client.constants import Entities
from search_client.opensearch import SearchClient, OpenSearchClientBuilder
from search_client.opensearch.configuration import SearchConfiguration


def prepare_results_for_response(models: list[BaseModel], serializers: dict[Entities: Type[Serializer]],
                                 raise_exception: bool = True) -> list[dict]:
    results = []
    for model in models:
        serializer = serializers[model.entity]
        result = serializer(data=model.model_dump(mode="json"))
        result.is_valid(raise_exception=raise_exception)
        results.append(result.data)
    return results


def get_opensearch_client() -> OpenSearch:
    host = settings.OPENSEARCH_HOST
    http_auth = None
    if "amazonaws.com" in host:
        http_auth = ("supersurf", settings.OPENSEARCH_PASSWORD)
    return OpenSearchClientBuilder.from_host(host, http_auth).build()


def get_search_client(configuration: SearchConfiguration = None, presets: list[str] = None) -> SearchClient:
    opensearch_client = get_opensearch_client()
    client = SearchClient(
        opensearch_client, settings.PLATFORM,
        presets=presets,
        configuration=configuration
    )
    if settings.OPENSEARCH_ALIAS_PREFIX:
        client.configuration.alias_prefix = settings.OPENSEARCH_ALIAS_PREFIX
    return client
