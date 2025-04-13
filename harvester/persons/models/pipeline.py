from django.db import models

from core.models.pipeline import BatchBase, ProcessResultBase


class Batch(BatchBase):
    documents = models.ManyToManyField(to="PersonDocument", through="ProcessResult")


class ProcessResult(ProcessResultBase):
    document = models.ForeignKey("PersonDocument", on_delete=models.CASCADE)
