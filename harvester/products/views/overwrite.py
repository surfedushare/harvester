from django.http import Http404
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated

from harvester.schema import HarvesterSchema
from core.loading import load_harvest_models
from products.models import Overwrite
from products.views.serializers.overwrite import ProductOverwriteSerializer


class ProductOverwriteListView(generics.ListAPIView):
    """
    Returns a list of all existing Overwrites.

    An Overwrite is a way for anybody to enrich/alter the data that is coming from sources.
    When documents from sources get indexed by the search engine
    the properties of an Overwrite will replace or supplement the values from source documents.
    The module responsible for loading data into the search engine may transform the format to suit the engine.
    """
    queryset = Overwrite.objects.filter(deleted_at__isnull=True)
    serializer_class = ProductOverwriteSerializer
    schema = HarvesterSchema()
    pagination_class = PageNumberPagination

    def get_serializer_context(self) -> None:
        context = super().get_serializer_context()
        storages = load_harvest_models("products")
        context["Document"] = storages.Document
        return context


class ProductOverwriteDetailView(generics.RetrieveUpdateAPIView):
    """
    This endpoint allows you to retrieve (GET), update (PUT, PATCH) an Overwrite.

    An Overwrite is a way for anybody to enrich/alter the data that is coming from sources.
    When documents from sources get indexed by the search engine
    the properties of an Overwrite will replace or supplement the values from source documents.
    The module responsible for loading data into the search engine may transform the format to suit the engine.

    ## Request body (create/update only)

    To update or create an Override you should PUT or PATCH it to this endpoint.
    Beware that a PUT may fail if other clients are trying to update an Overwrite at the exact same time.
    PATCH will wait for resource locks to be released, but it only allows to update a single property at a time.

    Notice that the properties that you can overwrite are restricted.
    Currently only "metrics" are allowed to be overwritten. Examples are star ratings and view counts.
    In the future "content" properties like title may also be modified through this API.

    Please consult the example request body below,
    to see the most up-to-date overview of which overwrites are possible.

    ## Response body

    The response contains an Overwrite. See request body to learn more about the properties of an Overwrite.
    Note that the module responsible for loading data into the search engine may transform the format of overwrites,
    to suit the engine.
    """
    queryset = Overwrite.objects.filter(deleted_at__isnull=True)
    serializer_class = ProductOverwriteSerializer
    lookup_url_kwarg = "srn"
    schema = HarvesterSchema()

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            self._is_create = True
            if self.request.method == "GET":
                raise
            return None

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if getattr(self, '_is_create', False):
            response.status_code = status.HTTP_201_CREATED
        return response

    def get_serializer_context(self) -> None:
        context = super().get_serializer_context()
        storages = load_harvest_models("products")
        context["Document"] = storages.Document
        context["DatasetVersion"] = storages.DatasetVersion
        return context

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [AllowAny()]
        return [IsAuthenticated()]
