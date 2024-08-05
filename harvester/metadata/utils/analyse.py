from invoke import Config
import requests
from collections import Counter, OrderedDict
from copy import copy

from django.conf import settings

from search_client import SearchClient
from system_configuration.main import create_configuration_and_session


class MetadataValueComparer:

    reference_environment = None
    reference_search = None
    reference_tree = None
    peer_environment = None
    peer_search = None

    @staticmethod
    def load_metadata_value_tree(environment: Config):
        metadata_tree_endpoint = f"{environment.django.protocol}://{environment.django.domain}/api/v1/metadata/tree/"
        response = requests.get(metadata_tree_endpoint, headers={
            "Authorization": f"Token {environment.secrets.harvester.api_key}"
        })
        if response.status_code != requests.status_codes.codes.OK:
            raise RuntimeError(f"Unable to load metadata values from: {metadata_tree_endpoint}; {response.status_code}")
        return response.json()

    @staticmethod
    def load_search_client(environment: Config) -> SearchClient:
        host = environment.opensearch.host
        document_type = settings.DOCUMENT_TYPE
        kwargs = {}
        if "amazonaws.com" in host:
            kwargs["basic_auth"] = ("supersurf", environment.secrets.opensearch.password,)
            kwargs["verify_certs"] = environment.opensearch.verify_certs
        return SearchClient(
            host,
            document_type,
            environment.opensearch.alias_prefix,
            **kwargs
        )

    def __init__(self, reference_environment, peer_environment) -> None:
        self.reference_environment, session = create_configuration_and_session()
        if reference_environment != self.reference_environment.service.env:
            raise ValueError("Reference environment should match APPLICATION_MODE")
        self.reference_search = self.load_search_client(self.reference_environment)
        self.reference_tree = self.load_metadata_value_tree(self.reference_environment)
        self.peer_environment, session = create_configuration_and_session(peer_environment)
        self.peer_search = self.load_search_client(self.peer_environment)

    def compare(self, value_filters: dict = None, fields: list[str] = None, cut_off: int = 0,
                limit: int = None) -> OrderedDict:

        fields = fields or [field["value"] for field in self.reference_tree]

        reference_results = self.reference_search.search("", drilldown_names=fields, filters=value_filters)
        reference_counts = Counter(**reference_results["drilldowns"])
        peer_results = self.peer_search.search("", drilldown_names=fields, filters=value_filters)
        peer_counts = Counter(**peer_results["drilldowns"])

        comparison_counts = copy(reference_counts)
        comparison_counts.subtract(peer_counts)
        comparison_items = [item for item in comparison_counts.items() if abs(item[1]) > cut_off]
        comparison_items.sort(key=lambda item: abs(item[1]), reverse=True)
        comparison_items = comparison_items[:limit]
        comparison = OrderedDict(comparison_items)

        return comparison
