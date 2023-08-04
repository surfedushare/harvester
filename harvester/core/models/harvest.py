from datetime import datetime, timedelta

from django.db import models
from django.utils.timezone import make_aware

from datagrowth.configuration import ConfigurationField

from sources.constants import DeletePolicies
from sources.models.harvest import HarvestEntity


class HarvestState(models.Model):

    entity = models.ForeignKey(HarvestEntity, on_delete=models.CASCADE)
    dataset = models.ForeignKey("Dataset", on_delete=models.CASCADE)
    harvest_set = models.ForeignKey("Set", on_delete=models.CASCADE, null=True, blank=True)

    config = ConfigurationField()
    set_specification = models.CharField(
        max_length=255,
        help_text="The code for the 'set' you want to harvest"
    )
    latest_update_at = models.DateTimeField(
        null=True, blank=True, default=make_aware(datetime(year=1970, month=1, day=1))
    )
    harvested_at = models.DateTimeField(null=True, blank=True)
    purge_after = models.DateTimeField(null=True, blank=True)

    def clean(self) -> None:
        if not self.purge_after:
            self.purge_after = make_aware(datetime.now()) + timedelta(**self.source.purge_interval)

    def should_purge(self) -> bool:
        return self.entity.delete_policy == DeletePolicies.NO or \
            (self.entity.delete_policy == DeletePolicies.TRANSIENT and self.purge_after and
             self.purge_after < make_aware(datetime.now()))

    def prepare(self) -> None:
        if self.harvested_at:
            self.latest_update_at = self.harvested_at
        self.save()

    def reset(self) -> None:
        self.latest_update_at = make_aware(datetime(year=1970, month=1, day=1))
        self.harvested_at = None
        self.purge_after = None
        self.clean()
        self.save()

    class Meta:
        abstract = True
