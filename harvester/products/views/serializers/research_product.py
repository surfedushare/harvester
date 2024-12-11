from rest_framework import serializers

from products.views.serializers.base import BaseSearchResultSerializer, AuthorSerializer


class ResearchProductResultSerializer(BaseSearchResultSerializer):

    doi = serializers.CharField(default=None, allow_null=True)
    type = serializers.CharField(allow_null=True)
    research_object_type = serializers.CharField(default=None, allow_null=True)
    parties = serializers.ListField(child=serializers.CharField())
    research_themes = serializers.ListField(child=serializers.CharField())
    projects = serializers.ListField(child=serializers.CharField())
    owners = AuthorSerializer(many=True)
    contacts = AuthorSerializer(many=True)
    subtitle = serializers.CharField(allow_null=True)
