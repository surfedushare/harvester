from django.db import models

from core.models.pipeline import BatchBase, ProcessResultBase


class Batch(BatchBase):
    documents = models.ManyToManyField(to="TestDocument", through="ProcessResult")


class ProcessResult(ProcessResultBase):
    document = models.ForeignKey("TestDocument", on_delete=models.CASCADE)
