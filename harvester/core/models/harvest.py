from datetime import datetime, timedelta

from django.apps import apps
from django.db import models
from django.utils.timezone import make_aware

from core.loading import load_harvest_models
from core.constants import DeletePolicies
from core.models.datatypes import HarvestDatasetVersion, HarvestSet


class HarvestState(models.Model):

    entity = models.ForeignKey("sources.HarvestEntity", on_delete=models.CASCADE, related_name="+")
    dataset = models.ForeignKey("Dataset", on_delete=models.CASCADE)
    harvest_set = models.ForeignKey("Set", on_delete=models.CASCADE, null=True, blank=True)

    harvested_at = models.DateTimeField(blank=True, default=make_aware(datetime(year=1970, month=1, day=1)))
    purge_after = models.DateTimeField(null=True, blank=True)

    def clean(self) -> None:
        if not self.purge_after:
            self.purge_after = make_aware(datetime.now()) + timedelta(**self.entity.purge_interval)

    @property
    def set_name(self):
        return f"{self.entity.source.module}:{self.entity.set_specification}"

    def should_purge(self) -> bool:
        return self.entity.delete_policy == DeletePolicies.NO or \
            (self.entity.delete_policy == DeletePolicies.TRANSIENT and self.purge_after and
             self.purge_after < make_aware(datetime.now()))

    def reset(self, dataset_version: HarvestDatasetVersion) -> HarvestSet:
        data_models = load_harvest_models(self.entity.type)
        self.harvested_at = self._meta.get_field("harvested_at").default
        self.purge_after = None
        self.harvest_set = data_models["Set"].objects.create(
            name=self.set_name,
            dataset_version=dataset_version,
            identifier="srn",
            delete_policy=self.entity.delete_policy
        )
        self.clean()
        self.save()
        return self.harvest_set

    def prepare_using_set(self, harvest_set: HarvestSet) -> HarvestSet:
        raise NotImplementedError("Not implemented yet")

    def clear_resources(self):
        for resource_name in self.entity.get_seeding_resources():
            resource = apps.get_model(resource_name)
            resource.objects.all().delete()

    class Meta:
        abstract = True
