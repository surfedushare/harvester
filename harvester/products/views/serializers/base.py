from dateutil.parser import parse as parse_datetime

from rest_framework import serializers


class BaseSearchResultSerializer(serializers.Serializer):

    srn = serializers.CharField(default=None)
    set = serializers.CharField(default=None)
    state = serializers.CharField(default="active")
    external_id = serializers.CharField()
    published_at = serializers.CharField(source="publisher_date", allow_blank=True, allow_null=True)
    modified_at = serializers.SerializerMethodField()
    url = serializers.URLField()
    title = serializers.CharField()
    description = serializers.CharField()
    language = serializers.CharField()
    copyright = serializers.CharField()
    video = serializers.DictField(default=None)
    harvest_source = serializers.CharField()
    previews = serializers.DictField(default=None)
    files = serializers.ListField(child=serializers.DictField())
    authors = serializers.ListField(child=serializers.DictField())
    has_parts = serializers.ListField(child=serializers.CharField())
    is_part_of = serializers.ListField(child=serializers.CharField())
    keywords = serializers.ListField(child=serializers.CharField())

    def get_modified_at(self, obj):
        modified_at = obj.get("modified_at")
        if not modified_at:
            return
        date = parse_datetime(modified_at)
        if not date:
            return
        return date.strftime("%Y-%m-%d")
