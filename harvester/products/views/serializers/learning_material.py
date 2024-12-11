from rest_framework import serializers

from products.views.serializers.base import BaseSearchResultSerializer


class SimpleLearningMaterialResultSerializer(BaseSearchResultSerializer):

    doi = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    lom_educational_levels = serializers.ListField(child=serializers.CharField())
    disciplines = serializers.ListField(child=serializers.CharField())
    study_vocabulary = serializers.ListField(child=serializers.CharField())
    technical_type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    material_types = serializers.ListField(child=serializers.CharField())
    aggregation_level = serializers.CharField(allow_blank=True, allow_null=True)
    publishers = serializers.ListField(child=serializers.CharField())
    consortium = serializers.CharField(allow_blank=True, allow_null=True)
    subtitle = serializers.CharField(allow_blank=True, allow_null=True)
