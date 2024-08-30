from django.conf import settings
from django.views.decorators.gzip import gzip_page
from django.utils.decorators import method_decorator
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError

from search_client.opensearch.client import SearchClient
from search_client.opensearch.configuration import is_valid_preset_search_configuration
from harvester.schema import HarvesterSchema
from metadata.models import MetadataField, MetadataFieldSerializer, MetadataValue, MetadataValueSerializer


@method_decorator(gzip_page, name="dispatch")
class MetadataTreeView(generics.ListAPIView):
    """
    The metadata tree is used for filtering with the full text search endpoint.
    This endpoint returns all available metadata values for a given entity or all values for products.

    There are two types of nodes in the metadata tree.
    The root metadata nodes have a **field** value of null.
    These nodes are all returned in the main array of the response and their type is MetadataField.
    You can filter and order search results on the value of a MetadataField.

    Other nodes are returned as the children of the MetadataField nodes.
    The type of these nodes is MetadataValue.
    You can use the value of these nodes as values you want to filter search results on.
    Typically for filtering search results you'll send the value of a MetadataField node,
    together with a number of values from MetadataValue nodes that are children of the chosen MetadataField,
    to the search endpoint.

    When filtering take note that if somebody selects a MetadataValue node that has children,
    then you'll want to send the values of these children together with the value of the parent
    as filter values in the search request. Failing to do this will yield unexpected results.

    ## Response body

    The response contains a list of metadata nodes. Each metadata node contains the following properties:

    **field**: The metadata field this node belongs to or null if the node is itself a metadata field.

    **parent**: The id of a parent node or null.

    **translation**: The translated display name of the metadata. Formerly the title_translations.

    **value**: Use this value to filter in the search endpoint. Formerly the external_id

    **is_hidden**: Whether this node should be visible for users.

    **children**: All nodes that have this node as a parent.

    **children_count**: Total number of children.
    When the max_children parameter is used this property will still reflect the true available amount of children.

    **frequency**: How many results match this node in the entire dataset.

    """
    serializer_class = MetadataFieldSerializer
    schema = HarvesterSchema()
    pagination_class = None

    def get_entities(self) -> list[str]:
        entity_input = self.request.GET.get("entity", SearchClient.preset_default)
        try:
            entity_validated_input = is_valid_preset_search_configuration(settings.PLATFORM, entity_input)
        except ValueError:
            raise ValidationError(f"Invalid entity for {settings.PLATFORM.value}: {entity_input}")
        entities = [entity_validated_input]
        if ":" in entity_input:
            entity, subtype = entity_input.split(":")
            entities.append(entity)
        else:
            entities.append(entity_input)
        return entities

    def get_queryset(self):
        entities = self.get_entities()
        return MetadataField.objects.filter(is_hidden=False).filter(entity__in=entities).select_related("translation")


@method_decorator(gzip_page, name="dispatch")
class MetadataFieldValuesView(generics.ListAPIView):

    queryset = MetadataValue.objects.filter(deleted_at__isnull=True)
    serializer_class = MetadataValueSerializer
    schema = HarvesterSchema()
    pagination_class = PageNumberPagination

    def filter_queryset(self, queryset):
        queryset = queryset.filter(field__name=self.kwargs["field"])
        startswith = self.kwargs.get("startswith", None)
        if startswith:
            queryset = queryset.filter(value__istartswith=startswith)
        field = MetadataField.objects.get(name=self.kwargs["field"])
        match field.value_output_order:
            case field.ValueOutputOrders.FREQUENCY:
                queryset = queryset.order_by("-frequency", "value")
            case field.ValueOutputOrders.ALPHABETICAL:
                queryset = queryset.order_by("value")
            case _:
                pass
        return queryset
