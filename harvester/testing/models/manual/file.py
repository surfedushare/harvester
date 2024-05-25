from copy import deepcopy
from hashlib import sha1

from django.conf import settings
from django.db import models
from django.dispatch import receiver

from core.models.datatypes.document import HarvestDocument
from files.constants import SEED_DEFAULTS
from testing.models.manual.document import ManualDocument, dispatch_manual_document
from testing.models.manual.product import TestProduct


def file_properties_default():
    defaults = deepcopy(SEED_DEFAULTS)
    defaults["state"] = HarvestDocument.States.ACTIVE
    defaults["access_rights"] = "OpenAccess"
    return defaults


class TestFile(ManualDocument):

    url = models.URLField()
    mime_type = models.CharField(choices=settings.MIME_TYPE_CHOICES, default="unknown")
    product = models.ForeignKey(TestProduct, on_delete=models.SET_NULL, null=True, blank=True)
    properties = models.JSONField(default=file_properties_default)

    def clean(self):
        super().clean()
        if not self.properties.get("url") or not self.properties.get("hash"):
            self.properties["url"] = self.url
            self.properties["hash"] = sha1(self.url.encode("utf-8")).hexdigest()
        if not self.properties.get("mime_type"):
            self.properties["mime_type"] = self.mime_type
        if self.product:
            self.properties["product_id"] = self.product.properties.get("srn")


@receiver(models.signals.post_save, sender=TestFile)
def dispatch_test_file(sender, instance, **kwargs):
    dispatch_manual_document(instance)
