from django.db import models

from core.models.pipeline import BatchBase, ProcessResultBase


class Batch(BatchBase):
    documents = models.ManyToManyField(to="ProductDocument", through="ProcessResult")


class ProcessResult(ProcessResultBase):
    document = models.ForeignKey("ProductDocument", on_delete=models.CASCADE)
