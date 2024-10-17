
from rest_framework import serializers


class ProjectSerializer(serializers.Serializer):

    entity = serializers.CharField()
    srn = serializers.CharField()
    set = serializers.CharField()
    state = serializers.CharField(default="active")
    external_id = serializers.CharField()
    score = serializers.FloatField(default=0.0)
    provider = serializers.CharField(default=None, allow_null=True)

    title = serializers.CharField(allow_null=True, allow_blank=True)
    description = serializers.CharField(allow_null=True, allow_blank=True)
    project_status = serializers.CharField(default="finished")
    started_at = serializers.DateField(allow_null=True)
    ended_at = serializers.DateField(allow_null=True)
    coordinates = serializers.ListField(child=serializers.FloatField())
    goal = serializers.CharField(allow_null=True, allow_blank=True)
    keywords = serializers.ListField(child=serializers.CharField())
    products = serializers.ListField(child=serializers.CharField())
    previews = serializers.DictField(default=None, allow_null=True)

    # Research project specific
    persons = serializers.ListField(child=serializers.DictField())
    contacts = serializers.ListField(child=serializers.DictField())
    owners = serializers.ListField(child=serializers.DictField())
    parties = serializers.ListField(child=serializers.CharField())
    themes = serializers.ListField(child=serializers.CharField())
    research_themes = serializers.ListField(child=serializers.CharField(), source="themes", default=list)
