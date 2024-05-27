from django.contrib import admin


class HarvestStateAdmin(admin.ModelAdmin):
    list_display = ("entity", "dataset", "set_specification", "harvested_at", "is_harvesting")
    list_filter = ("entity", "dataset",)

    def is_harvesting(self, obj):
        return bool(obj.harvest_set and (obj.harvest_set.pending_at or obj.harvest_set.dataset_version.pending_at))
    is_harvesting.boolean = True
