from django.shortcuts import Http404
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from testing.utils.generators import seed_generator


ENTITY_SEQUENCE_PROPERTIES = {
    "simple": {
        "srn": "surf:testing:{ix}",
        "external_id": "{ix}",  # will be cast to an int
        "url": "http://localhost:8888/file/{ix}",
        "title": "title for {ix}"
    }
}


class EntityMockAPIView(APIView):

    permission_classes = (AllowAny,)

    def get(self, request, entity):
        size = int(request.GET.get("size", 20))
        sequence_properties = ENTITY_SEQUENCE_PROPERTIES.get(entity, None)
        seeds = list(seed_generator(entity, size, sequence_properties))
        paginator = PageNumberPagination()
        paginator.page_size_query_param = "page_size"
        page_data = paginator.paginate_queryset(seeds, request, view=self)
        return paginator.get_paginated_response(data=page_data)


class EntityMockIdListAPIView(APIView):

    permission_classes = (AllowAny,)

    def get(self, request, entity):
        size = int(request.GET.get("size", 20))
        sequence_properties = ENTITY_SEQUENCE_PROPERTIES.get(entity, None)
        seeds = list(seed_generator(entity, size, sequence_properties))
        return Response([{"id": obj["external_id"]} for obj in seeds])


class EntityMockDetailAPIView(APIView):

    permission_classes = (AllowAny,)

    def get(self, request, pk, entity):
        size = int(request.GET.get("size", 20))
        sequence_properties = ENTITY_SEQUENCE_PROPERTIES.get(entity, None)
        seeds = list(seed_generator(entity, size, sequence_properties))
        try:
            return Response(next((obj for obj in seeds if str(obj["external_id"]) == pk)))
        except StopIteration:
            raise Http404(f"Object with primary key not found: {pk}")
