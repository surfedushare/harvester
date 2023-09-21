from urllib.parse import unquote

from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.status import HTTP_417_EXPECTATION_FAILED

from harvester.schema import HarvesterSchema
from harvester.pagination import HarvesterPageNumberPagination
from core.loading import load_harvest_models


class NoCurrentDatasetVersionException(Exception):
    pass


class DatasetVersionDocumentBaseView(generics.GenericAPIView):

    schema = HarvesterSchema()

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
        return dataset_version.documents.all()


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


class SearchDocumentListViewMixin(object):

    def get_serializer(self, *args, **kwargs):
        if len(args):
            objects = [list(doc.to_search())[0] for doc in args[0]]
            args = (objects, *args[1:])
        return super().get_serializer(*args, **kwargs)


class SearchDocumentRetrieveViewMixin(object):

    def get_serializer(self, *args, **kwargs):
        if len(args):
            obj = list(args[0].to_search())[0]
            args = (obj, *args[1:])
        return super().get_serializer(*args, **kwargs)
