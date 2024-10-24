from rest_framework import serializers

from datagrowth.datatypes.views import DocumentBaseSerializer
from search_client.constants import Entities
from core.views.document import (DatasetVersionDocumentListView, DatasetVersionDocumentDetailView,
                                 SearchDocumentListViewMixin, SearchDocumentRetrieveViewMixin)
from products.models import ProductDocument


class RawProductDocumentSerializer(DocumentBaseSerializer):

    class Meta:
        model = ProductDocument
        fields = DocumentBaseSerializer.default_fields + ("state", "metadata", "derivatives")


class MetadataProductDocumentSerializer(serializers.ModelSerializer):

    srn = serializers.CharField(source="identity")
    title = serializers.CharField(source="properties.title")
    language = serializers.CharField(source="properties.language")
    created_at = serializers.DateTimeField(source="metadata.created_at")
    modified_at = serializers.DateTimeField(source="metadata.modified_at")
    reference = serializers.CharField(source="properties.external_id")

    class Meta:
        model = ProductDocument
        fields = ("id", "state", "srn", "title", "reference", "language", "created_at", "modified_at")


class RawProductListView(DatasetVersionDocumentListView):
    """
    Returns a list of the most recent products.
    The dataformat is an internal dataformat which is not guaranteed to remain constant over time.
    This endpoint is mostly meant for debugging purposes.
    """
    serializer_class = RawProductDocumentSerializer


class MetadataProductListView(DatasetVersionDocumentListView):
    """
    Returns a list of the most recent products, but it only returns the metadata.
    This is useful for things like a sitemap where only the metadata is important.
    """
    serializer_class = MetadataProductDocumentSerializer
    exclude_deletes_unless_modified_since_filter = True


class RawProductDetailView(DatasetVersionDocumentDetailView):
    """
    Returns the most recent version of a product using its SURF Resource Name as an identifier.
    The dataformat is an internal dataformat which is not guaranteed to remain constant over time.
    This endpoint is mostly meant for debugging purposes.
    """
    serializer_class = RawProductDocumentSerializer


class MetadataProductDetailView(DatasetVersionDocumentDetailView):
    """
    Returns the most recent version of a product using its SURF Resource Name as an identifier,
    but it only returns the metadata. This is useful for things like a sitemap where only the metadata is important.
    """
    serializer_class = MetadataProductDocumentSerializer
    exclude_deletes_unless_modified_since_filter = True


class SearchProductListView(SearchDocumentListViewMixin, DatasetVersionDocumentListView):
    """
    Returns a list of the most recent products.
    The dataformat is identical to how a search endpoint would return the product.
    This endpoint is useful for systems that want a local copy of all possible search results.

    When using the ``modified_since`` parameter the products will be limited to products that have been modified
    by this service since that date. Note that this service may decide to refresh data,
    even though sources didn't change that data.

    Most properties for a ProductDocument are automatically documented through the interactive documentation.
    However there are a few special properties that we'll document here.

    **authors**: The list of authors for a ProductDocument.
    Authors are objects with the following properties: name, email, external_id, dai, orcid and isni.
    All these properties have string values or are null.

    **files**: The list of files for a ProductDocument.
    Files are objects with the following properties: title, url, mime_type, hash, copyright and access_rights.
    All these properties have string values or are null.
    The hash of a file is a sha1 hash of the file URL and doesn't represent the content of a file.
    The copyright and access_rights properties have values as defined in the NL-LOM standard.

    **previews**: For a product that supports thumbnails this object will contain three image links:
    preview, full_size and preview_small. Where preview is 400x300 pixels and small_preview 200x150 pixels in size.
    The full_size image varies in size, but will be the largest possible image.

    **video**: For a product with a video that supports additional metadata this object will contain
    the duration and the embed_url of that video
    """
    entity = Entities.PRODUCTS
    exclude_deletes_unless_modified_since_filter = True


class SearchProductDetailView(SearchDocumentRetrieveViewMixin, DatasetVersionDocumentDetailView):
    """
    Returns the most recent version of a product, using its SURF Resource Name as an identifier,
    in the same format a search result would return it.
    This is useful if a system wants to update their copy of a product.

    Most properties for a ProductDocument are automatically documented through the interactive documentation.
    However there are a few special properties that we'll document here.

    **authors**: The list of authors for a ProductDocument.
    Authors are objects with the following properties: name, email, external_id, dai, orcid and isni.
    All these properties have string values or are null.

    **files**: The list of files for a ProductDocument.
    Files are objects with the following properties: title, url, mime_type, hash, copyright and access_rights.
    All these properties have string values or are null.
    The hash of a file is a sha1 hash of the file URL and doesn't represent the content of a file.
    The copyright and access_rights properties have values as defined in the NL-LOM standard.

    **previews**: For a product that supports thumbnails this object will contain three image links:
    preview, full_size and preview_small. Where preview is 400x300 pixels and small_preview 200x150 pixels in size.
    The full_size image varies in size, but will be the largest possible image.

    **video**: For a product with a video that supports additional metadata this object will contain
    the duration and the embed_url of that video
    """
    entity = Entities.PRODUCTS
    exclude_deletes_unless_modified_since_filter = True
