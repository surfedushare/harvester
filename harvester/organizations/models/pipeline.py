from django.db import models

from core.models.pipeline import BatchBase, ProcessResultBase


class Batch(BatchBase):
    documents = models.ManyToManyField(to="OrganizationDocument", through="ProcessResult")


class ProcessResult(ProcessResultBase):
    document = models.ForeignKey("OrganizationDocument", on_delete=models.CASCADE)
