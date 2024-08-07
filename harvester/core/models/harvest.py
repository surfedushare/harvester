from datetime import datetime, timedelta

from django.apps import apps
from django.db import models
from django.utils.timezone import make_aware, now

from datagrowth.utils import ibatch
from core.constants import DeletePolicies
from core.loading import load_harvest_models
from core.models.datatypes import HarvestDatasetVersion, HarvestSet


class HarvestState(models.Model):

    entity = models.ForeignKey("sources.HarvestEntity", on_delete=models.CASCADE, related_name="+")
    dataset = models.ForeignKey("Dataset", on_delete=models.CASCADE)
    harvest_set = models.ForeignKey("Set", on_delete=models.SET_NULL, null=True, blank=True)

    set_specification = models.CharField(
        max_length=255,
        help_text="The slug for the 'set' you want to harvest",
        db_index=True
    )
    harvested_at = models.DateTimeField(
        blank=True,
        default=make_aware(datetime(year=1970, month=1, day=1)),
        db_index=True
    )
    purge_after = models.DateTimeField(null=True, blank=True, db_index=True)

    def clean(self) -> None:
        if not self.purge_after:
            self.purge_after = make_aware(datetime.now()) + timedelta(**self.entity.purge_interval)

    @property
    def set_name(self):
        return f"{self.entity.source.module}:{self.set_specification}"

    def should_purge(self) -> bool:
        return self.purge_after and self.purge_after < now()

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

    def prepare_using_set(self, dataset_version: HarvestDatasetVersion, harvest_set: HarvestSet) -> HarvestSet:
        current_time = now()
        data_models = load_harvest_models(self.entity.type)
        self.harvest_set = data_models["Set"].objects.create(
            name=self.set_name,
            dataset_version=dataset_version,
            identifier="srn",
            delete_policy=self.entity.delete_policy
        )
        self.clean()
        self.save()
        for batch in ibatch(harvest_set.documents.all(), batch_size=100):
            documents = []
            for document in batch:
                document.prepare_task_processing(current_time=current_time)
                # Copy the instance in the database
                document.pk = None
                document.id = None
                document.collection = self.harvest_set
                document.dataset_version = dataset_version
                if self.entity.delete_policy == DeletePolicies.NO and not self.entity.is_manual:
                    # Here we soft delete all Documents where delete_policy is "no".
                    # This gets undone by any incoming document, which enables us to
                    # look at deleted_at to detect deleted Documents during check_set_integrity task.
                    document.metadata["deleted_at"] = current_time
                document.clean(set_metadata=False)  # retains "metadata" from copy, but links new Set and DatasetVersion
                documents.append(document)
            data_models["Document"].objects.bulk_create(documents)
        return self.harvest_set

    def clear_resources(self):
        for resource_name in self.entity.get_seeding_resources():
            resource = apps.get_model(resource_name)
            resource.objects.all().delete()

    class Meta:
        abstract = True
