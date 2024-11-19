from django.db import models

from core.models.pipeline import BatchBase, ProcessResultBase


class Batch(BatchBase):
    documents = models.ManyToManyField(to="ProjectDocument", through="ProcessResult")


class ProcessResult(ProcessResultBase):
    document = models.ForeignKey("ProjectDocument", on_delete=models.CASCADE)
