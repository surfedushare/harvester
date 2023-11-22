from django.db import models

from core.models.pipeline import BatchBase, ProcessResultBase


class Batch(BatchBase):
    documents = models.ManyToManyField(to="FileDocument", through="ProcessResult")


class ProcessResult(ProcessResultBase):
    document = models.ForeignKey("FileDocument", on_delete=models.CASCADE)
