from copy import deepcopy

from django.db import models
from django.dispatch import receiver

from core.models.datatypes.document import HarvestDocument
from products.constants import SEED_DEFAULTS
from testing.models.manual.document import ManualDocument, dispatch_manual_document


def product_properties_default():
    defaults = deepcopy(SEED_DEFAULTS)
    defaults["state"] = HarvestDocument.States.ACTIVE
    defaults["authors"].append({
        "dai": None,
        "isni": None,
        "name": "Test de Tester",
        "email": None,
        "orcid": None,
        "external_id": "harvester:person:x"
    })
    return defaults


class TestProduct(ManualDocument):

    properties = models.JSONField(default=product_properties_default)

    def clean(self):
        super().clean()
        if self.modified_at:
            self.properties["modified_at"] = self.modified_at.isoformat()


@receiver(models.signals.post_save, sender=TestProduct)
def dispatch_test_product(sender, instance, **kwargs):
    dispatch_manual_document(instance)
