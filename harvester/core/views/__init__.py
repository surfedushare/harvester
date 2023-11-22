from .legacy.document import (RawDocumentListView, RawDocumentDetailView, MetadataDocumentListView,
                              MetadataDocumentDetailView, SearchDocumentListView, SearchDocumentDetailView)
from .legacy.dataset import DatasetListView, DatasetDetailView, DatasetDocumentsView, DatasetMetadataDocumentsView
from .extension import ExtensionListView, ExtensionDetailView
from .health import health_check
from .query import QueryViewSet
