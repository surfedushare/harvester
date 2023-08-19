from datetime import datetime, timedelta

from django.db import models
from django.utils.timezone import make_aware

from datagrowth.configuration import ConfigurationField

from sources.constants import DeletePolicies


class HarvestState(models.Model):

    entity = models.ForeignKey("sources.HarvestEntity", on_delete=models.CASCADE, related_name="+")
    dataset = models.ForeignKey("Dataset", on_delete=models.CASCADE)
    harvest_set = models.ForeignKey("Set", on_delete=models.CASCADE, null=True, blank=True)

    config = ConfigurationField()
    harvested_at = models.DateTimeField(blank=True, default=make_aware(datetime(year=1970, month=1, day=1)))
    purge_after = models.DateTimeField(null=True, blank=True)

    def clean(self) -> None:
        if not self.purge_after:
            self.purge_after = make_aware(datetime.now()) + timedelta(**self.entity.purge_interval)

    def should_purge(self) -> bool:
        return self.entity.delete_policy == DeletePolicies.NO or \
            (self.entity.delete_policy == DeletePolicies.TRANSIENT and self.purge_after and
             self.purge_after < make_aware(datetime.now()))

    def reset(self) -> None:
        self.harvested_at = None
        self.purge_after = None
        self.clean()
        self.save()

    class Meta:
        abstract = True
