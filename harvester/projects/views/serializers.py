from django.core.validators import MinLengthValidator, MaxLengthValidator
from rest_framework import serializers


class ContactSerializer(serializers.Serializer):
    name = serializers.CharField(allow_null=True, default=None)
    email = serializers.EmailField(allow_null=True, default=None)
    external_id = serializers.CharField(allow_null=True, default=None)


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
    coordinates = serializers.ListField(
        child=serializers.FloatField(),
        validators=[MinLengthValidator(0), MaxLengthValidator(2)]
    )
    goal = serializers.CharField(allow_null=True, allow_blank=True)
    approach = serializers.CharField(allow_null=True, allow_blank=True)
    results = serializers.CharField(allow_null=True, allow_blank=True)
    keywords = serializers.ListField(child=serializers.CharField())
    products = serializers.ListField(child=serializers.CharField())
    previews = serializers.DictField(default=None, allow_null=True)
    photo_url = serializers.CharField(allow_null=True, allow_blank=True)

    # Research project specific
    persons = ContactSerializer(many=True)
    contacts = ContactSerializer(many=True)
    owners = ContactSerializer(many=True)
    parties = serializers.ListField(child=serializers.CharField())
    themes = serializers.ListField(child=serializers.CharField())
    research_themes = serializers.ListField(child=serializers.CharField(), source="themes", default=list)
    sia_project_reference = serializers.CharField(allow_null=True, default=None)
