from django.db import models

from core.loading import load_source_configuration
from core.constants import DeletePolicies, DELETE_POLICY_CHOICES


def thirty_days_default():
    return {"days": 30}


class HarvestSource(models.Model):

    name = models.CharField(max_length=50, help_text="Human readable name")
    module = models.CharField(max_length=50, help_text="Name of Python modules related to this source", db_index=True)
    is_repository = models.BooleanField(
        default=False,
        help_text="Enable when source is a repository for multiple providers"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.module


class HarvestEntity(models.Model):

    class EntityType(models.TextChoices):
        PRODUCT = "products", "Product"
        FILE = "files", "File"
        PROJECTS = "projects", "Project"
        TEST = "testing", "Test"

    source = models.ForeignKey(HarvestSource, on_delete=models.CASCADE)
    type = models.CharField(choices=EntityType.choices, max_length=50, db_index=True)

    is_available = models.BooleanField(default=False)
    is_manual = models.BooleanField(default=False)
    allows_update = models.BooleanField(default=False)

    set_specifications = models.JSONField(
        default=list, blank=True,
        help_text="The slugs for the 'sets' you want to harvest"
    )
    delete_policy = models.CharField(max_length=50, choices=DELETE_POLICY_CHOICES, default=DeletePolicies.TRANSIENT)
    purge_interval = models.JSONField(default=thirty_days_default)

    def get_seeding_resources(self):
        configuration = load_source_configuration(self.type, self.source.module)
        return [
            phase.get("retrieve_data").get("resource")
            for phase in configuration["seeding_phases"] if phase.get("retrieve_data", None)
        ]

    def __str__(self) -> str:
        return f"{self.source}.{self.type}"

    class Meta:
        unique_together = ("source", "type",)
        verbose_name_plural = "harvest entities"
