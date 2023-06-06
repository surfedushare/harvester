from urllib.parse import unquote

from django.conf import settings
from rest_framework import generics
from rest_framework import serializers
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.status import HTTP_417_EXPECTATION_FAILED

from datagrowth.datatypes.views import DocumentBaseSerializer
from search_client.serializers import SimpleLearningMaterialResultSerializer, ResearchProductResultSerializer
from search_client.constants import DocumentTypes
from harvester.schema import HarvesterSchema
from harvester.pagination import HarvesterPageNumberPagination
from core.models import Document, DatasetVersion


class NoCurrentDatasetVersionException(Exception):
    pass


class DocumentSerializer(DocumentBaseSerializer):

    harvest_source = serializers.CharField(source="collection.name")
    feed = serializers.CharField(source="collection.name")
    properties = serializers.SerializerMethodField()

    def get_properties(self, document):
        properties = document.properties
        properties["owners"] = [next(iter(properties["authors"]), None)]
        properties["contacts"] = [next(iter(properties["authors"]), None)]
        return properties

    class Meta:
        model = Document
        fields = DocumentBaseSerializer.default_fields + ("harvest_source", "feed",)


class MetadataDocumentSerializer(DocumentBaseSerializer):

    language = serializers.CharField(source="properties.language.metadata")

    class Meta:
        model = Document
        fields = ("id", "reference", "language", "created_at", "modified_at")


class DatasetVersionDocumentBaseView(generics.GenericAPIView):

    document_type = settings.DOCUMENT_TYPE
    schema = HarvesterSchema()

    def get_queryset(self):
        dataset_version = DatasetVersion.objects.get_current_version()
        if not dataset_version:
            raise NoCurrentDatasetVersionException()
        return dataset_version.document_set.all()


class DatasetVersionDocumentListView(ListModelMixin, DatasetVersionDocumentBaseView):

    pagination_class = HarvesterPageNumberPagination

    def get(self, request, *args, **kwargs):
        try:
            return self.list(request, *args, **kwargs)
        except NoCurrentDatasetVersionException:
            return Response(
                {"detail": "Missing a current dataset version to list data"},
                status=HTTP_417_EXPECTATION_FAILED
            )


class RawDocumentListView(DatasetVersionDocumentListView):
    """
    Returns a list of the most recent documents.
    The dataformat is an internal dataformat which is not guaranteed to remain constant over time.
    This endpoint is mostly meant for debugging purposes.
    """
    serializer_class = DocumentSerializer


class MetadataDocumentListView(DatasetVersionDocumentListView):
    """
    Returns a list of the most recent documents, but it only returns the metadata.
    This is useful for things like a sitemap where only the metadata is important.
    """
    serializer_class = MetadataDocumentSerializer


class SearchDocumentGenericViewMixin(object):

    document_type = settings.DOCUMENT_TYPE

    def get_serializer_class(self):
        if self.document_type == DocumentTypes.LEARNING_MATERIAL:
            return SimpleLearningMaterialResultSerializer
        elif self.document_type == DocumentTypes.RESEARCH_PRODUCT:
            return ResearchProductResultSerializer
        else:
            raise AssertionError("DocumentListView expected application to use different DOCUMENT_TYPE")


class SearchDocumentListView(SearchDocumentGenericViewMixin, DatasetVersionDocumentListView):
    """
    Returns a list of the most recent documents.
    The dataformat is identical to how a search endpoint would return the document.
    This endpoint is useful for systems that want a local copy of all possible search results.
    """

    def get_serializer(self, *args, **kwargs):
        if len(args):
            objects = [list(doc.to_search())[0] for doc in args[0]]
            args = (objects, *args[1:])
        return super().get_serializer(*args, **kwargs)


class DatasetVersionDocumentDetailView(RetrieveModelMixin, DatasetVersionDocumentBaseView):

    def get_object(self):
        queryset = self.get_queryset()
        reference = unquote(self.kwargs["external_id"])
        return queryset.get(reference=reference)

    def get(self, request, *args, **kwargs):
        try:
            return self.retrieve(request, *args, **kwargs)
        except NoCurrentDatasetVersionException:
            return Response(
                {"detail": "Missing a current dataset version to retrieve data"},
                status=HTTP_417_EXPECTATION_FAILED
            )


class RawDocumentDetailView(DatasetVersionDocumentDetailView):
    """
    Returns the most recent version of a document.
    The dataformat is an internal dataformat which is not guaranteed to remain constant over time.
    This endpoint is mostly meant for debugging purposes.
    """
    serializer_class = DocumentSerializer


class MetadataDocumentDetailView(DatasetVersionDocumentDetailView):
    """
    Returns the most recent version of a document, but it only returns the metadata.
    This is useful for things like a sitemap where only the metadata is important.
    """
    serializer_class = MetadataDocumentSerializer


class SearchDocumentDetailView(SearchDocumentGenericViewMixin, DatasetVersionDocumentDetailView):
    """
    Returns the most recent version of a document in the same format a search result would return it.
    This is useful if a system wants to update their copy of a document.
    """

    def get_serializer(self, *args, **kwargs):
        if len(args):
            obj = list(args[0].to_search())[0]
            args = (obj, *args[1:])
        return super().get_serializer(*args, **kwargs)
