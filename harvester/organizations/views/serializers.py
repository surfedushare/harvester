from rest_framework import serializers


class SimpleOrganizationSerializer(serializers.Serializer):
    srn = serializers.CharField()
    name = serializers.CharField(allow_null=True, allow_blank=False)
    ror = serializers.CharField(allow_null=True, allow_blank=False)
    is_root = serializers.BooleanField(default=None, allow_null=True)


class OrganizationSerializer(serializers.Serializer):

    entity = serializers.CharField()
    srn = serializers.CharField()
    set = serializers.CharField()
    provider = serializers.CharField(default=None, allow_null=True)
    state = serializers.CharField(default="active")

    name = serializers.CharField(allow_null=True, allow_blank=False)
    description = serializers.CharField(allow_null=True, allow_blank=False)
    ror = serializers.CharField(allow_null=True, allow_blank=False)
    type = serializers.CharField(allow_null=False, allow_blank=False)
    is_root = serializers.BooleanField(default=None, allow_null=True)
    secretary = SimpleOrganizationSerializer()
    parents = SimpleOrganizationSerializer(many=True)
    members = SimpleOrganizationSerializer(many=True)
