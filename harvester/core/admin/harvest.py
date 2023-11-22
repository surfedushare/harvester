from django.contrib import admin

from core.models import HarvestSource


class HarvestSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "spec", "delete_policy", "created_at", "modified_at",)


class HarvestAdminInline(admin.TabularInline):
    model = HarvestSource.datasets.through
    fields = ("source", "harvested_at", "latest_update_at", "purge_after", "stage", "is_syncing",)
    readonly_fields = ("harvested_at",)
    extra = 0


class HarvestStateAdmin(admin.ModelAdmin):
    list_display = ("entity", "dataset", "set_specification", "harvested_at", "is_harvesting")
    list_filter = ("entity", "dataset",)

    def is_harvesting(self, obj):
        return bool(obj.harvest_set and (obj.harvest_set.pending_at or obj.harvest_set.dataset_version.pending_at))
    is_harvesting.boolean = True
