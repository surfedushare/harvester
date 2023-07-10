from django.db import models
from django.utils import timezone

from datagrowth.datatypes import DocumentBase


class Extension(DocumentBase):

    id = models.CharField(primary_key=True, max_length=100)
    dataset_version = models.ForeignKey("DatasetVersion", blank=True, null=True, on_delete=models.CASCADE)
    # NB: Collection foreign key is added by the base class
    is_addition = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(default=None, null=True, blank=True)

    def restore(self):
        self.deleted_at = None
        self.save()

    def delete(self, using=None, keep_parents=False):
        if not self.deleted_at and self.is_addition:
            self.deleted_at = timezone.now()
            self.save()
        else:
            super().delete(using=using, keep_parents=keep_parents)
