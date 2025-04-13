from rest_framework import serializers


class PersonSerializer(serializers.Serializer):

    entity = serializers.CharField()
    srn = serializers.CharField()
    set = serializers.CharField()
    state = serializers.CharField(default="active")
    external_id = serializers.CharField()
    score = serializers.FloatField(default=0.0)
    provider = serializers.CharField(default=None, allow_null=True)

    name = serializers.CharField(allow_null=True, default=None)
    first_name = serializers.CharField(allow_null=True, default=None)
    last_name = serializers.CharField(allow_null=True, default=None)
    prefix = serializers.CharField(allow_null=True, default=None)
    initials = serializers.CharField(allow_null=True, default=None)

    email = serializers.EmailField(allow_null=True, default=None)
    phone = serializers.CharField(allow_null=True, default=None)
    photo_url = serializers.CharField(allow_null=True, allow_blank=False)
    description = serializers.CharField(allow_null=True, default=None)

    isni = serializers.CharField(allow_null=True, default=None)

    skills = serializers.ListField(child=serializers.CharField())
    organizations = serializers.ListField(child=serializers.CharField())
    is_employed = serializers.BooleanField(allow_null=True, default=None)
    job_title = serializers.CharField(allow_null=True, default=None)


class ResearcherSerializer(PersonSerializer):
    parties = serializers.ListField(child=serializers.CharField(), source="organizations")
    title = serializers.CharField(allow_null=True, default=None)
    themes = serializers.ListField(child=serializers.CharField())
    orcid = serializers.CharField(allow_null=True, default=None)
    dai = serializers.CharField(allow_null=True, default=None)
