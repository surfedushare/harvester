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

    class Meta:
        abstract = True
