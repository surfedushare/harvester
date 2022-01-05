"""
This module contains implementation of REST API views for communities app.
"""

import logging

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from surf.apps.communities.models import Community, Team
from surf.apps.communities.serializers import CommunitySerializer

from surf.apps.materials.models import Collection
from surf.apps.materials.serializers import (
    CollectionSerializer,
    CollectionShortSerializer
)


logger = logging.getLogger(__name__)


class CommunityViewSet(ListModelMixin,
                       RetrieveModelMixin,
                       UpdateModelMixin,
                       GenericViewSet):
    """
    View class that provides `GET` and `UPDATE` methods for Community.
    """

    queryset = Community.objects.filter(deleted_at=None)
    serializer_class = CommunitySerializer
    permission_classes = []

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        if self.request.method != 'GET':
            check_access_to_community(self.request.user, obj)
        return obj

    @action(methods=['get', 'post', 'put', 'delete'], detail=True)
    def collections(self, request, pk=None, **kwargs):
        """
        Returns community collections
        """

        instance = self.get_object()

        qs = instance.collections.filter(deleted_at=None).order_by("position")
        if request.method in {"POST", "DELETE", "PUT"}:
            # validate request parameters
            serializer = CollectionSerializer(many=True, data=request.data) if request.method == "POST" else \
                CollectionShortSerializer(many=True, data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.initial_data
            collection_ids = [d["id"] for d in data]
            if request.method == "POST":
                self._add_collections(instance, data)
                qs = qs.filter(id__in=collection_ids)

            elif request.method == "PUT":
                self._update_collections(instance, data)
                qs = qs.filter(id__in=collection_ids)

            elif request.method == "DELETE":
                self._delete_collections(instance, data)
                return Response()

        qs = qs.annotate(community_cnt=Count('communities', filter=Q(deleted_at=None)))

        if request.method == "GET":
            page = self.paginate_queryset(qs)
            if page is not None:
                serializer = CollectionSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        res = CollectionSerializer(many=True).to_representation(qs.all())
        return Response(res)

    @staticmethod
    def _add_collections(instance, collections):
        """
        Adds collections to community
        :param instance: community instance
        :param collections: added collections
        :return:
        """

        collections = [c["id"] for c in collections]
        collections = Collection.objects.filter(id__in=collections).all()
        instance.collections.add(*collections)

    @staticmethod
    def _update_collections(instance, collections):
        """
        Updates collection positions for a community
        :param instance: community instance
        :param collections: collections
        :return:
        """
        updated_collections = []
        for collection in collections:
            updated_collection = Collection.objects.get(id=collection["id"])
            updated_collection.position = collection["position"]
            updated_collection.save()
            updated_collections.append(updated_collection)
        return Response(updated_collections)

    @staticmethod
    def _delete_collections(instance, collections):
        """
        Deletes collections from community
        :param instance: community instance
        :param collections: collections that should be deleted
        :return:
        """
        collections = [c["id"] for c in collections]
        collections = Collection.objects.filter(id__in=collections).all()
        instance.collections.remove(*collections)


def check_access_to_community(user, instance=None):
    """
    Check if user is active and admin of community
    :param user: user
    :param instance: community instance
    added/deleted to/from community
    """
    if not user or not user.is_authenticated:
        raise AuthenticationFailed()
    try:
        Team.objects.get(community=instance, user=user)
    except ObjectDoesNotExist as exc:
        raise AuthenticationFailed(f"User {user} is not a member of community {instance}. Error: \"{exc}\"")
    except MultipleObjectsReturned as exc:
        # if somehow there are user duplicates on a community, don't crash
        logger.warning(f"User {user} is in community {instance} multiple times. Error: \"{exc}\"")
