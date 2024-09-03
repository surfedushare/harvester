from rest_framework import serializers

from products.views.serializers.base import BaseSearchResultSerializer


class ResearchProductResultSerializer(BaseSearchResultSerializer):

    doi = serializers.CharField(default=None, allow_null=True)
    type = serializers.CharField(allow_null=True)
    research_object_type = serializers.CharField(default=None, allow_null=True)
    parties = serializers.ListField(child=serializers.CharField(), default=[])
    research_themes = serializers.ListField(child=serializers.CharField(), default=[])
    projects = serializers.ListField(child=serializers.CharField(), default=[])
    owners = serializers.ListField(child=serializers.DictField(), default=[])
    contacts = serializers.ListField(child=serializers.DictField(), default=[])
    subtitle = serializers.CharField(allow_null=True)
