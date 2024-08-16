from rest_framework import serializers


class BaseSearchResultSerializer(serializers.Serializer):

    srn = serializers.CharField(default=None)
    set = serializers.CharField(default=None)
    state = serializers.CharField(default="active")
    external_id = serializers.CharField()
    provider = serializers.CharField(default=None, allow_null=True)
    published_at = serializers.CharField(allow_null=True)
    modified_at = serializers.DateField(allow_null=True)
    url = serializers.URLField()
    title = serializers.CharField()
    description = serializers.CharField()
    language = serializers.CharField()
    copyright = serializers.CharField()
    video = serializers.DictField(default=None, allow_null=True)
    harvest_source = serializers.CharField()
    previews = serializers.DictField(default=None, allow_null=True)
    files = serializers.ListField(child=serializers.DictField())
    authors = serializers.ListField(child=serializers.DictField())
    has_parts = serializers.ListField(child=serializers.CharField())
    is_part_of = serializers.ListField(child=serializers.CharField())
    keywords = serializers.ListField(child=serializers.CharField())
