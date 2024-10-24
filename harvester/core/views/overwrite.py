from typing import Type

from django.db import transaction, DatabaseError
from django.utils.timezone import now
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError, APIException

from datagrowth.datatypes.views import DocumentBaseSerializer
from core.models.datatypes import HarvestDocument, HarvestOverwrite


class LockConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Unable to acquire lock - resource is currently being modified.'
    default_code = 'lock_conflict'


class MetricsOverwriteSerializer(serializers.Serializer):
    views = serializers.IntegerField(default=0, min_value=0)
    star_1 = serializers.IntegerField(default=0, min_value=0)
    star_2 = serializers.IntegerField(default=0, min_value=0)
    star_3 = serializers.IntegerField(default=0, min_value=0)
    star_4 = serializers.IntegerField(default=0, min_value=0)
    star_5 = serializers.IntegerField(default=0, min_value=0)


class OverwriteSerializer(DocumentBaseSerializer):

    id = serializers.CharField(read_only=True)
    srn = serializers.CharField(write_only=True)

    def validate_metrics(self, metrics: dict):
        metrics_serializer = MetricsOverwriteSerializer(data=metrics)
        metrics_serializer.is_valid(raise_exception=True)
        validated_metrics = metrics_serializer.validated_data
        if self.partial:
            if sum([value for value in validated_metrics.values()]) != 1:
                raise ValidationError("Patch request can only update a single metric at a time.")
        return validated_metrics

    def validate(self, attrs: dict):
        Document: Type[HarvestDocument] = self.context["Document"]
        srn = attrs["srn"]
        if srn != self.context["view"].kwargs["srn"]:
            raise ValidationError("SRN of request path and body doesn't match.")
        if not Document.objects.filter(identity=srn).exists():
            raise ValidationError(
                f"Could not find Document with srn '{srn}'."
            )
        return super().validate(attrs)

    def create(self, validated_data):
        srn = validated_data.pop("srn")
        metrics = validated_data.pop("metrics")
        overwrite = super().create({
            "id": srn,
            "properties": {
                "metrics": metrics,
            }
        })
        Document: Type[HarvestDocument] = self.context["Document"]
        Document.objects.filter(identity=srn).update(modified_at=now(), overwrite=overwrite)
        return overwrite

    def partial_update(self, instance: HarvestOverwrite, validated_data: dict):
        # Acquire a lock on the specified Overwrite
        # And write metrics data as the sum of old and new data.
        Document: Type[HarvestDocument] = self.context["Document"]
        Overwrite: Type[HarvestOverwrite] = self.Meta.model
        with transaction.atomic():
            overwrite, created = Overwrite.objects.select_for_update(nowait=False).get_or_create(pk=instance.pk)
        srn = validated_data.pop("srn")
        metrics = validated_data["metrics"]
        for metric, value in metrics.items():
            overwrite.properties["metrics"][metric] += value
        from devtools import debug
        debug(overwrite.properties)
        overwrite.save()
        # Update modified_at for all possible documents as all documents have essentially changed with the Overwrite.
        Document.objects.filter(identity=srn).update(modified_at=now())
        return overwrite

    def update(self, instance: HarvestOverwrite, validated_data):
        if self.partial:
            return self.partial_update(instance, validated_data)
        # Acquire a lock on the specified Overwrite
        # And write data as the new Overwrite properties
        Document: Type[HarvestDocument] = self.context["Document"]
        Overwrite: Type[HarvestOverwrite] = self.Meta.model
        with transaction.atomic():
            try:
                overwrite, created = Overwrite.objects.select_for_update(nowait=True).get_or_create(pk=instance.pk)
            except DatabaseError:
                raise LockConflictError()
        srn = validated_data.pop("srn")
        overwrite.properties = validated_data
        overwrite.save()
        # Update modified_at for all possible documents as all documents have essentially changed with the Overwrite.
        Document.objects.filter(identity=srn).update(modified_at=now())
        return overwrite
