from django.db import models
from django.utils import timezone

from datagrowth.datatypes import DocumentBase


class HarvestOverwrite(DocumentBase):

    id = models.CharField(primary_key=True, max_length=100)
    collection = models.ForeignKey("Set", blank=True, null=True, on_delete=models.CASCADE)
    properties = models.JSONField(default=dict)
    deleted_at = models.DateTimeField(default=None, null=True, blank=True)

    def restore(self) -> None:
        self.deleted_at = None
        self.save()

    def delete(self, using=None, keep_parents=False) -> None:
        if not self.deleted_at:
            self.deleted_at = timezone.now()
            self.save()
        else:
            super().delete(using=using, keep_parents=keep_parents)

    def get_metrics_overwrite(self) -> dict:
        metrics = self.properties.get("metrics", {})
        if not metrics:
            return {
                "views": 0,
                "stars": {
                    "average": 0.0,
                    "star_1": 0,
                    "star_2": 0,
                    "star_3": 0,
                    "star_4": 0,
                    "star_5": 0,
                }
            }
        # TODO: add calculations
        # TODO: add index fields for boost on search

    def __str__(self) -> str:
        return self.id

    class Meta:
        abstract = True
