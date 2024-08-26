from typing import Type
from urllib.parse import unquote

from django.apps import apps
from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.status import HTTP_417_EXPECTATION_FAILED
from pydantic import BaseModel

from harvester.schema import HarvesterSchema
from harvester.pagination import HarvesterPageNumberPagination
from core.loading import load_harvest_models
from core.models.datatypes import HarvestDocument


class NoCurrentDatasetVersionException(Exception):
    pass


class DatasetVersionDocumentBaseView(generics.GenericAPIView):
    """
    This generic view will load the correct DatasetVersion based on the request.resolver_match.
    The DatasetVersion instance returns the queryset for the views or raises a NoCurrentDatasetVersionException.
    """

    schema = HarvesterSchema()
    exclude_deletes_unless_modified_since_filter = False

    def get_queryset(self):
        if not self.request.resolver_match:
            return Response(
                {"detail": "Missing an app_name for view to load correct models"},
                status=HTTP_417_EXPECTATION_FAILED
            )
        version, app_label = self.request.resolver_match.app_name.split(":")
        models = load_harvest_models(app_label)
        dataset_version = models["DatasetVersion"].objects.get_current_version()
        if not dataset_version:
            raise NoCurrentDatasetVersionException()
        modified_since_filter = self.request.query_params.get("modified_since")
        if self.exclude_deletes_unless_modified_since_filter and not modified_since_filter:
            queryset = dataset_version.documents.filter(state=HarvestDocument.States.ACTIVE)
        else:
            queryset = dataset_version.documents.all()
        if modified_since_filter:
            queryset = queryset.filter(metadata__modified_at__gte=modified_since_filter)
        queryset = queryset.order_by("-id")
        return queryset


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


class DatasetVersionDocumentDetailView(RetrieveModelMixin, DatasetVersionDocumentBaseView):

    def get_object(self):
        queryset = self.get_queryset()
        identity = unquote(self.kwargs["srn"])
        return get_object_or_404(queryset, identity=identity)

    def get(self, request, *args, **kwargs):
        try:
            return self.retrieve(request, *args, **kwargs)
        except NoCurrentDatasetVersionException:
            return Response(
                {"detail": "Missing a current dataset version to retrieve data"},
                status=HTTP_417_EXPECTATION_FAILED
            )


class SearchDocumentGenericViewMixin:
    """
    This generic view helps to load the correct serializer and data transformer based on the entity attribute.

    NB: This class and subclasses can't look at request.resolver_match to determine the entity,
    because get_serializer_class needs a static definition for the documentation generator.
    """

    entity = None

    def get_serializer_class(self):
        app_config = apps.get_app_config(self.entity.value)
        return app_config.result_serializer

    @classmethod
    def get_transformer_class(cls) -> Type[BaseModel]:
        app_config = apps.get_app_config(cls.entity.value)
        return app_config.result_transformer


class SearchDocumentListViewMixin(SearchDocumentGenericViewMixin):

    def get_queryset(self):
        queryset = super().get_queryset()
        modified_since_filter = self.request.query_params.get("modified_since")
        if modified_since_filter:
            queryset = queryset.filter(metadata__modified_at__gte=modified_since_filter)
        return queryset

    def get_serializer(self, *args, **kwargs):
        transformer = self.get_transformer_class()
        if len(args):
            objects = [
                transformer(**doc.to_data()).model_dump(mode="json")
                for doc in args[0]
            ]
            args = (objects, *args[1:])
        return super().get_serializer(*args, **kwargs)


class SearchDocumentRetrieveViewMixin(SearchDocumentGenericViewMixin):

    def get_serializer(self, *args, **kwargs):
        transformer = self.get_transformer_class()
        if len(args):
            obj = transformer(**args[0].to_data()).model_dump(mode="json")
            args = (obj, *args[1:])
        return super().get_serializer(*args, **kwargs)
