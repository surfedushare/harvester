from rest_framework import serializers

from datagrowth.datatypes.views import DocumentBaseSerializer
from search_client.constants import Entities
from core.views.document import (DatasetVersionDocumentListView, DatasetVersionDocumentDetailView,
                                 SearchDocumentListViewMixin, SearchDocumentRetrieveViewMixin)
from projects.models import ProjectDocument


class RawProjectDocumentSerializer(DocumentBaseSerializer):

    class Meta:
        model = ProjectDocument
        fields = DocumentBaseSerializer.default_fields + ("state", "metadata", "derivatives")


class MetadataProjectDocumentSerializer(serializers.ModelSerializer):

    srn = serializers.CharField(source="identity")
    title = serializers.CharField(source="properties.title")
    language = serializers.CharField(source="properties.language")
    created_at = serializers.DateTimeField(source="metadata.created_at")
    modified_at = serializers.DateTimeField(source="metadata.modified_at")
    reference = serializers.CharField(source="properties.external_id")

    class Meta:
        model = ProjectDocument
        fields = ("id", "state", "srn", "title", "reference", "language", "created_at", "modified_at")


class RawProjectListView(DatasetVersionDocumentListView):
    """
    Returns a list of the most recent products.
    The dataformat is an internal dataformat which is not guaranteed to remain constant over time.
    This endpoint is mostly meant for debugging purposes.
    """
    serializer_class = RawProjectDocumentSerializer


class MetadataProjectListView(DatasetVersionDocumentListView):
    """
    Returns a list of the most recent products, but it only returns the metadata.
    This is useful for things like a sitemap where only the metadata is important.
    """
    serializer_class = MetadataProjectDocumentSerializer
    exclude_deletes_unless_modified_since_filter = True


class RawProjectDetailView(DatasetVersionDocumentDetailView):
    """
    Returns the most recent version of a product using its SURF Resource Name as an identifier.
    The dataformat is an internal dataformat which is not guaranteed to remain constant over time.
    This endpoint is mostly meant for debugging purposes.
    """
    serializer_class = RawProjectDocumentSerializer


class MetadataProjectDetailView(DatasetVersionDocumentDetailView):
    """
    Returns the most recent version of a product using its SURF Resource Name as an identifier,
    but it only returns the metadata. This is useful for things like a sitemap where only the metadata is important.
    """
    serializer_class = MetadataProjectDocumentSerializer
    exclude_deletes_unless_modified_since_filter = True


class SearchProjectListView(SearchDocumentListViewMixin, DatasetVersionDocumentListView):
    """
    Returns a list of the most recent projects.
    The dataformat is identical to how a search endpoint would return the project.
    This endpoint is useful for systems that want a local copy of all possible search results.
    """
    entity = Entities.PROJECTS
    exclude_deletes_unless_modified_since_filter = True


class SearchProjectDetailView(SearchDocumentRetrieveViewMixin, DatasetVersionDocumentDetailView):
    """
    Returns the most recent version of a project, using its SURF Resource Name as an identifier,
    in the same format a search result would return it.
    This is useful if a system wants to update their copy of a project.
    """
    entity = Entities.PROJECTS
    exclude_deletes_unless_modified_since_filter = True
