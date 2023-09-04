from copy import deepcopy

from django.shortcuts import Http404
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.models.datatypes.document import HarvestDocument
from testing.utils.generators import seed_generator
from testing.constants import ENTITY_SEQUENCE_PROPERTIES


class EntityMockAPIView(APIView):

    permission_classes = (AllowAny,)

    def get(self, request, entity):
        # Generate the basic seeds
        size = int(request.GET.get("size", 20))
        sequence_properties = ENTITY_SEQUENCE_PROPERTIES.get(entity, None)
        seeds = list(seed_generator(entity, size, sequence_properties))

        # Delete some seeds if necessary
        deletes = int(request.GET.get("deletes", 0))
        if deletes:
            for ix, seed in enumerate(seeds):
                if not ix % deletes:
                    seed["state"] = HarvestDocument.States.DELETED.value

        # Generate some nested seeds if required and divide those among the main generated seeds
        nested_entity = request.GET.get("nested", None)
        if nested_entity:
            nested_sequence_properties = ENTITY_SEQUENCE_PROPERTIES.get(entity, None)
            nested_seeds = list(seed_generator(nested_entity, size, nested_sequence_properties))
            for ix, seed in enumerate(seeds):
                nested = []
                nested_length = ix % 3
                for _ in range(0, nested_length):
                    nested.append(nested_seeds.pop(0))
                seed[f"{nested_entity}s"] = deepcopy(nested) if seed["state"] != HarvestDocument.States.DELETED.value \
                    else []

        # Return the paginator
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
        delete_ids = []

        deletes = int(request.GET.get("deletes", 0))
        if deletes:
            for ix, seed in enumerate(seeds):
                if not ix % deletes:
                    delete_ids.append(seed["external_id"])

        return Response([{"id": obj["external_id"]} for obj in seeds if obj["external_id"] not in delete_ids])


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
