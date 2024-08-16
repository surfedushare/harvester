from urllib.parse import unquote

from django.conf import settings
from django.core.validators import MinValueValidator
from django.shortcuts import Http404
from rest_framework.generics import GenericAPIView
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from search_client.constants import Platforms, Entities

from harvester.schema import HarvesterSchema
from metadata.models import MetadataField
from search.clients import get_search_client, prepare_results_for_response
from search.views.base import load_results_serializers
from products.views.serializers import SimpleLearningMaterialResultSerializer, ResearchProductResultSerializer


class DocumentSearchFilterSerializer(serializers.Serializer):

    external_id = serializers.CharField()
    items = serializers.ListField(child=serializers.CharField(allow_null=True))


class DocumentSearchSerializer(serializers.Serializer):

    search_text = serializers.CharField(required=True, allow_blank=True, write_only=True)
    filters = DocumentSearchFilterSerializer(many=True, write_only=True, default=[])
    ordering = serializers.CharField(required=False, allow_blank=True, default=None, allow_null=True, write_only=True)

    page = serializers.IntegerField(required=False, default=1, validators=[MinValueValidator(1)])
    page_size = serializers.IntegerField(required=False, default=10, validators=[MinValueValidator(0)])

    results_total = serializers.DictField(read_only=True)

    def validate_filters(self, filters):
        if not filters:
            return filters
        filter_fields = self.context.get("filter_fields", None)
        for metadata_filter in filters:
            field_id = metadata_filter.get("external_id", None)
            if field_id not in filter_fields:
                raise ValidationError(detail=f"Invalid external_id for metadata field in filter: '{field_id}'")
        return filters

    def validate_ordering(self, ordering):
        if not ordering:
            return
        filter_fields = self.context.get("filter_fields", [])
        ordering_field = ordering[1:] if ordering.startswith("-") else ordering
        if ordering_field not in filter_fields:
            raise ValidationError(detail=f"Invalid value for ordering: '{ordering}'")
        return ordering


class LearningMaterialSearchSerializer(DocumentSearchSerializer):
    results = SimpleLearningMaterialResultSerializer(many=True, read_only=True)


class ResearchProductSearchSerializer(DocumentSearchSerializer):
    results = ResearchProductResultSerializer(many=True, read_only=True)


class DocumentSearchAPIView(GenericAPIView):
    """
    The main search endpoint.
    Specify the search query in the **search_text** property of the body to do a simple search.
    All other properties are optional and are described below

    ## Request body

    Apart from search_text you can specify the following properties in the body of the request:

    **page_size**: Number of results to return per page.

    **page**: A page number within the paginated result set.

    **filters**: Filters consist of an array of objects that specify an external_id and an items property.
    The external_id should be the value of a MetadataField (for instance: "technical_type").
    See the metadata tree endpoint for more details on MetadataField and their values.
    Next to the external_id you should specify an array under the items property.
    Elements in this array should only consist of values from MetadataValue nodes (for instance: "video").
    Again see the metadata tree endpoint for more details on MetadataValue.

    Filters using the same MetadataField, by specifying multiple values in the items array,
    will function as OR filters.
    While specifying multiple MetadataValues, in the items arrays across different MetadataFields,
    function as AND filters.

    The only exception to the above is how filtering works for a date range.
    When you specify "publisher_date" as the external_id of a filter,
    then the first item in the items array is a lower bound.
    While the second item is the upper bound.
    For each boundary it's possible to specify a null value meaning that there is no boundary.
    If you specify ["1970-01-01", null] it will filter the search to results with a **publisher_date** after 01-01-1970
    and until the present day. Anything lacking a **publisher_date** will be filtered out.

    **ordering**: The value of a MetadataField to order results by (for instance: "publisher_date").
    See the metadata tree endpoint for more details on MetadataField and their values.
    Ordering results like this will mostly ignore relevance of results and order by the specified field.
    By default ordering is ascending.
    If you specify the minus sign (for instance: "-publisher_date") the ordering will be descending.

    ## Response body

    **results**: An array containing the search results.

    **results_total**: Object with information about the total amount of found documents.
    The "value" key gives the found documents count. The "is_precise" key is true when the value is exact
    or false when it indicates the lower bound.

    **page_size**: Number of results to return per page.

    **page**: The current page number.

    """
    permission_classes = (AllowAny,)
    schema = HarvesterSchema()

    def get_serializer_class(self):
        if settings.PLATFORM is Platforms.EDUSOURCES:
            return LearningMaterialSearchSerializer
        elif settings.PLATFORM is Platforms.PUBLINOVA:
            return ResearchProductSearchSerializer
        else:
            raise AssertionError("DocumentSearchAPIView expected application to use different PLATFORM")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["filter_fields"] = MetadataField.objects.all().values_list("name", flat=True)
        return context

    def post(self, request, *args, **kwargs):
        # Validate request parameters and prepare search
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        include_filter_counts = request.GET.get("include_filter_counts", None) == "1"
        if not data["search_text"] and not data["ordering"]:
            data["ordering"] = "-publisher_date"
        # Execute search and return results
        client = get_search_client()
        response = client.search(aggregate_filter_counts=include_filter_counts, **data)
        result_serializer = load_results_serializers(request, single_serializer=True)
        results = prepare_results_for_response(response["results"], result_serializer[Entities.PRODUCTS])
        return Response({
            "results": results,
            "results_total": response["results_total"],
            "did_you_mean": response["did_you_mean"],
            "page": data["page"],
            "page_size": data["page_size"],
            "filter_counts": response.get("aggregations", response["drilldowns"]) if include_filter_counts else None
        })


class DocumentSearchDetailAPIView(GenericAPIView):
    """
    Searches for a document with the specified external_id.
    It raises a 404 if the document is not found.
    Otherwise it returns the document as an object.
    """

    permission_classes = (AllowAny,)
    schema = HarvesterSchema()

    def get_serializer_class(self):
        if settings.PLATFORM is Platforms.EDUSOURCES:
            return SimpleLearningMaterialResultSerializer
        elif settings.PLATFORM is Platforms.PUBLINOVA:
            return ResearchProductResultSerializer
        else:
            raise AssertionError("DocumentSearchDetailAPIView expected application to use different PLATFORM")

    def get_object(self):
        client = get_search_client()
        reference = unquote(self.kwargs["external_id"])
        response = client.get_documents_by_id([reference])
        results = response.get("results", [])
        if not results:
            raise Http404()
        document = results[0]
        return document.model_dump(mode="json")

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response(instance)


class LearningMaterialDetailsSerializer(serializers.Serializer):
    external_ids = serializers.ListField(child=serializers.CharField(), write_only=True)
    results = SimpleLearningMaterialResultSerializer(many=True, read_only=True)
    results_total = serializers.DictField(read_only=True)


class ResearchProductDetailsSerializer(serializers.Serializer):
    external_ids = serializers.ListField(child=serializers.CharField(), write_only=True)
    results = ResearchProductResultSerializer(many=True, read_only=True)
    results_total = serializers.DictField(read_only=True)


class DocumentSearchDetailsAPIView(GenericAPIView):
    """
    Searches for documents with the specified external ids.

    ## Request body

    **external_ids**: A list of external ids to find documents for

    ## Response body

    **results**: The list of documents that match the external ids

    **results_total**: Object with information about the total amount of found documents.
    The "value" key gives the found documents count. This could be less than the amount of given external ids
    if some of the external ids weren't found. The "is_precise" key is true when the value is exact
    or false when it indicates the lower bound.
    """

    permission_classes = (AllowAny,)
    schema = HarvesterSchema()
    max_page_size = 100

    def get_serializer_class(self):
        if settings.PLATFORM is Platforms.EDUSOURCES:
            return LearningMaterialDetailsSerializer
        elif settings.PLATFORM is Platforms.PUBLINOVA:
            return ResearchProductDetailsSerializer
        else:
            raise AssertionError("DocumentSearchDetailsAPIView expected application to use different PLATFORM")

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        external_ids = serializer.validated_data["external_ids"]
        if len(external_ids) > self.max_page_size:
            raise ValidationError(detail=f"Can't process more than {self.max_page_size} external ids at a time")
        client = get_search_client()
        response = client.get_documents_by_id(external_ids, page_size=self.max_page_size)
        result_serializer = load_results_serializers(request, single_serializer=True)
        results = prepare_results_for_response(response.get("results", []), result_serializer[Entities.PRODUCTS])
        return Response({
            "results": results,
            "results_total": {
                "value": len(results),
                "is_precise": True
            }
        })
