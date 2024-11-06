from rest_framework import serializers

from datagrowth.datatypes.views import DocumentBaseSerializer
from search_client.constants import Entities
from core.views.document import (DatasetVersionDocumentListView, DatasetVersionDocumentDetailView,
                                 SearchDocumentListViewMixin, SearchDocumentRetrieveViewMixin)
from organizations.models import OrganizationDocument


class RawOrganizationDocumentSerializer(DocumentBaseSerializer):

    class Meta:
        model = OrganizationDocument
        fields = DocumentBaseSerializer.default_fields + ("state", "metadata", "derivatives")


class MetadataOrganizationDocumentSerializer(serializers.ModelSerializer):

    srn = serializers.CharField(source="identity")
    name = serializers.CharField(source="properties.name")
    created_at = serializers.DateTimeField(source="metadata.created_at")
    modified_at = serializers.DateTimeField(source="metadata.modified_at")
    reference = serializers.CharField(source="properties.external_id")

    class Meta:
        model = OrganizationDocument
        fields = ("id", "state", "srn", "name", "reference", "created_at", "modified_at")


class RawOrganizationListView(DatasetVersionDocumentListView):
    """
    Returns a list of the most recent organizations.
    The dataformat is an internal dataformat which is not guaranteed to remain constant over time.
    This endpoint is mostly meant for debugging purposes.
    """
    serializer_class = RawOrganizationDocumentSerializer


class MetadataOrganizationListView(DatasetVersionDocumentListView):
    """
    Returns a list of the most recent organizations, but it only returns the metadata.
    This is useful for things like a sitemap where only the metadata is important.
    """
    serializer_class = MetadataOrganizationDocumentSerializer
    exclude_deletes_unless_modified_since_filter = True


class RawOrganizationDetailView(DatasetVersionDocumentDetailView):
    """
    Returns the most recent version of an organization using its SURF Resource Name as an identifier.
    The dataformat is an internal dataformat which is not guaranteed to remain constant over time.
    This endpoint is mostly meant for debugging purposes.
    """
    serializer_class = RawOrganizationDocumentSerializer


class MetadataOrganizationDetailView(DatasetVersionDocumentDetailView):
    """
    Returns the most recent version of an organization using its SURF Resource Name as an identifier,
    but it only returns the metadata. This is useful for things like a sitemap where only the metadata is important.
    """
    serializer_class = MetadataOrganizationDocumentSerializer
    exclude_deletes_unless_modified_since_filter = True


class OrganizationListView(SearchDocumentListViewMixin, DatasetVersionDocumentListView):
    """
    Returns a list of the most recent organizations.
    The dataformat is considered stable within an API version.
    This endpoint is useful for systems that want a local copy of all possible organizations.

    When using the ``modified_since`` parameter the organizations will be limited to organizations
    that have been modified by this service since that date. Note that this service may decide to refresh data,
    even though sources didn't change that data.

    Most properties for an OrganizationDocument are automatically documented through the interactive documentation.
    However there are a few special properties that we'll document here.

    # TODO: fill out the gaps, rename base classes
    """
    entity = "organizations"
    exclude_deletes_unless_modified_since_filter = True


class OrganizationDetailView(SearchDocumentRetrieveViewMixin, DatasetVersionDocumentDetailView):
    """
    Returns the most recent version of an organization, using its SURF Resource Name as an identifier,
    in a stable format within an API version.
    This is useful if a system wants to update their copy of an organization.

    Most properties for an OrganizationDocument are automatically documented through the interactive documentation.
    However there are a few special properties that we'll document here.

    # TODO: fill out the gaps, rename base classes
    """
    entity = "organizations"
    exclude_deletes_unless_modified_since_filter = True
