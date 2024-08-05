from rest_framework import serializers

from products.views.serializers.base import BaseSearchResultSerializer


class ResearchProductResultSerializer(BaseSearchResultSerializer):

    provider = serializers.SerializerMethodField()
    doi = serializers.SerializerMethodField()
    type = serializers.CharField(source="technical_type")
    research_object_type = serializers.CharField()
    parties = serializers.ListField(child=serializers.CharField(), source="publishers")
    research_themes = serializers.ListField(child=serializers.CharField())
    projects = serializers.ListField(child=serializers.CharField(), default=[])
    owners = serializers.SerializerMethodField(method_name="list_first_author")
    contacts = serializers.SerializerMethodField(method_name="list_first_author")
    subtitle = serializers.SerializerMethodField()

    def get_provider(self, obj):
        provider = obj["provider"]
        if provider["name"]:
            return provider["name"]
        elif provider["slug"]:
            return provider["slug"]
        elif provider["ror"]:
            return provider["ror"]
        elif provider["external_id"]:
            return provider["external_id"]

    def get_doi(self, obj):
        doi = obj.get("doi", None)
        if not doi:
            return
        return "https://doi.org/" + doi

    def list_first_author(self, obj):
        authors = obj.get("authors", None)
        if not authors:
            return []
        return [authors[0]]

    def get_subtitle(self, obj):
        subtitle = obj.get("subtitle")
        if not subtitle:
            return
        title = obj.get("title", "")
        return subtitle if subtitle not in title else None
