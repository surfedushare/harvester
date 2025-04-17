from rest_framework import serializers
from datagrowth.datatypes.views import DocumentBaseSerializer

from core.views.document import (DatasetVersionDocumentListView, DatasetVersionDocumentDetailView,
                                 SearchDocumentListViewMixin as TransformDocumentListViewMixin,
                                 SearchDocumentRetrieveViewMixin as TransformDocumentRetrieveViewMixin)
from persons.models import PersonDocument


class RawPersonDocumentSerializer(DocumentBaseSerializer):

    class Meta:
        model = PersonDocument
        fields = DocumentBaseSerializer.default_fields + ("state", "metadata", "derivatives")


class MetadataPersonDocumentSerializer(serializers.ModelSerializer):

    srn = serializers.CharField(source="identity")
    name = serializers.CharField(source="properties.author.name")
    created_at = serializers.DateTimeField(source="metadata.created_at")
    modified_at = serializers.DateTimeField(source="metadata.modified_at")
    reference = serializers.CharField(source="properties.external_id")

    class Meta:
        model = PersonDocument
        fields = ("id", "state", "srn", "name", "reference", "created_at", "modified_at")


class RawPersonListView(DatasetVersionDocumentListView):
    """
    Returns a list of the most recent persons.
    The dataformat is an internal dataformat which is not guaranteed to remain constant over time.
    This endpoint is mostly meant for debugging purposes.
    """
    serializer_class = RawPersonDocumentSerializer


class MetadataPersonListView(DatasetVersionDocumentListView):
    """
    Returns a list of the most recent persons, but it only returns the metadata.
    This is useful for things like a sitemap where only the metadata is important.
    """
    serializer_class = MetadataPersonDocumentSerializer
    exclude_deletes_unless_modified_since_filter = True


class RawPersonDetailView(DatasetVersionDocumentDetailView):
    """
    Returns the most recent version of a person using its SURF Resource Name as an identifier.
    The dataformat is an internal dataformat which is not guaranteed to remain constant over time.
    This endpoint is mostly meant for debugging purposes.
    """
    serializer_class = RawPersonDocumentSerializer


class MetadataPersonDetailView(DatasetVersionDocumentDetailView):
    """
    Returns the most recent version of a person using its SURF Resource Name as an identifier,
    but it only returns the metadata. This is useful for things like a sitemap where only the metadata is important.
    """
    serializer_class = MetadataPersonDocumentSerializer
    exclude_deletes_unless_modified_since_filter = True


class PersonListView(TransformDocumentListViewMixin, DatasetVersionDocumentListView):
    """
    Returns a list of the most recent persons.
    The dataformat is considered stable within an API version.
    This endpoint is useful for systems that want a local copy of all possible persons.

    When using the ``modified_since`` parameter the persons will be limited to persons
    that have been modified by this service since that date. Note that this service may decide to refresh data,
    even though sources didn't change that data.
    """
    entity = "persons"
    exclude_deletes_unless_modified_since_filter = True


class PersonDetailView(TransformDocumentRetrieveViewMixin, DatasetVersionDocumentDetailView):
    """
    Returns the most recent version of a person, using its SURF Resource Name as an identifier,
    in a stable format within an API version.
    This is useful if a system wants to update their copy of a person.
    """
    entity = "persons"
    exclude_deletes_unless_modified_since_filter = True
