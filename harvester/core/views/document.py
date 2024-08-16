from typing import Type
from urllib.parse import unquote

from django.conf import settings
from pydantic import BaseModel
from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.status import HTTP_417_EXPECTATION_FAILED

from search_client.constants import Platforms
from search_client.serializers import LearningMaterial, ResearchProduct
from harvester.schema import HarvesterSchema
from harvester.pagination import HarvesterPageNumberPagination
from core.loading import load_harvest_models
from core.models.datatypes import HarvestDocument


class NoCurrentDatasetVersionException(Exception):
    pass


class DatasetVersionDocumentBaseView(generics.GenericAPIView):

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


def load_pydantic_product_model() -> Type[BaseModel]:
    if settings.PLATFORM is Platforms.EDUSOURCES:
        return LearningMaterial
    elif settings.PLATFORM is Platforms.PUBLINOVA:
        return ResearchProduct
    else:
        raise AssertionError("SearchProductGenericViewMixin expected application to use different PLATFORM")


class SearchDocumentListViewMixin:

    def get_queryset(self):
        queryset = super().get_queryset()
        modified_since_filter = self.request.query_params.get("modified_since")
        if modified_since_filter:
            queryset = queryset.filter(metadata__modified_at__gte=modified_since_filter)
        return queryset

    def get_serializer(self, *args, **kwargs):
        model = load_pydantic_product_model()
        if len(args):
            objects = [
                model(**doc.to_data()).model_dump(mode="json")
                for doc in args[0]
            ]
            args = (objects, *args[1:])
        return super().get_serializer(*args, **kwargs)


class SearchDocumentRetrieveViewMixin:

    def get_serializer(self, *args, **kwargs):
        model = load_pydantic_product_model()
        if len(args):
            obj = model(**args[0].to_data()).model_dump(mode="json")
            args = (obj, *args[1:])
        return super().get_serializer(*args, **kwargs)
