from urllib.parse import unquote

from django.conf import settings
from rest_framework import generics
from rest_framework.generics import get_object_or_404
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

    def get_serializer_class(self):
        if settings.DOCUMENT_TYPE == DocumentTypes.LEARNING_MATERIAL:
            return SimpleLearningMaterialResultSerializer
        elif settings.DOCUMENT_TYPE == DocumentTypes.RESEARCH_PRODUCT:
            return ResearchProductResultSerializer
        else:
            raise AssertionError("DocumentListView expected application to use different DOCUMENT_TYPE")


class SearchDocumentListView(SearchDocumentGenericViewMixin, DatasetVersionDocumentListView):
    """
    Returns a list of the most recent documents.
    The dataformat is identical to how a search endpoint would return the document.
    This endpoint is useful for systems that want a local copy of all possible search results.

    Most properties for a Document are automatically documented through the interactive documentation.
    However there are three special properties that we'll document here.

    **authors**: The list of authors for a Document.
    Authors are objects with the following properties: name, email, external_id, dai, orcid and isni.
    All these properties have string values or are null.

    **files**: The list of files for a Document.
    Files are objects with the following properties: title, url, mime_type, hash, copyright and access_rights.
    All these properties have string values or are null.
    The hash of a file is a sha1 hash of the file URL and doesn't represent the content of a file.
    The copyright and access_rights properties have values as defined in the NL-LOM standard.

    **extension**: An object indicating the Extension active upon a Document.
    An Extension consists of two properties: id and is_addition.
    The id is numeric. The is_addition property indicates whether the Extension adds a new Document
    or updates a Document from a source. Usually this value will be false.

    **previews**: For a document that supports thumbnails this object will contain three image links:
    preview, full_size and preview_small. Where preview is 400x300 pixels and small_preview 200x150 pixels in size.
    The full_size image varies in size, but will be the largest possible image.

    **video**: For a document with a video that supports additional metadata this object will contain
    the duration and the embed_url of that video
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
        return get_object_or_404(queryset, reference=reference)

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

    Most properties for a Document are automatically documented through the interactive documentation.
    However there are two special properties that we'll document here.

    **authors**: The list of authors for a Document.
    Authors are objects with the following properties: name, email, external_id, dai, orcid and isni.
    All these properties have string values or are null.

    **files**: The list of files for a Document.
    Files are objects with the following properties: title, url, mime_type, hash, copyright and access_rights.
    All these properties have string values or are null.
    The hash of a file is a sha1 hash of the file URL and doesn't represent the content of a file.
    The copyright and access_rights properties have values as defined in the NL-LOM standard.

    **previews**: For a document that supports thumbnails this object will contain three image links:
    preview, full_size and preview_small. Where preview is 400x300 pixels and small_preview 200x150 pixels in size.
    The full_size image varies in size, but will be the largest possible image.

    **video**: For a document with a video that supports additional metadata this object will contain
    the duration and the embed_url of that video
    """

    def get_serializer(self, *args, **kwargs):
        if len(args):
            obj = list(args[0].to_search())[0]
            args = (obj, *args[1:])
        return super().get_serializer(*args, **kwargs)
