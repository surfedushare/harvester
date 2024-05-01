from django.contrib import admin, messages
from django.utils.timezone import now

from datagrowth.admin import HttpResourceAdmin
from core.loading import load_harvest_models
from sources.models import (HanOAIPMHResource, HvaPureResource, HkuMetadataResource, GreeniOAIPMHResource,
                            BuasPureResource, HanzeResearchObjectResource, PublinovaMetadataResource,
                            EdurepJsonSearchResource, SaxionOAIPMHResource, AnatomyToolOAIPMH, EdurepOAIPMH)
from sources.models.harvest import HarvestSource, HarvestEntity


class HarvestSourceAdmin(admin.ModelAdmin):

    list_display = ("name", "module", "is_repository",)
    actions = ["purge_source_harvest_states"]

    def purge_source_harvest_states(self, request, queryset):
        current_time = now()
        update_count = 0
        entity_types = set()
        for entity in HarvestEntity.objects.filter(source__in=queryset):
            models = load_harvest_models(entity.type)
            update_count += models["HarvestState"].objects.filter(entity=entity).update(purge_after=current_time)
            entity_types.add(entity.type)
        entities = ", ".join(entity_types)
        messages.info(request, f"Purged {update_count} harvest states for: {entities}")


class HarvestEntityAdmin(admin.ModelAdmin):
    list_display = ("source", "type", "is_available", "is_manual")
    list_filter = ("source", "type",)


admin.site.register(HanOAIPMHResource, HttpResourceAdmin)
admin.site.register(HvaPureResource, HttpResourceAdmin)
admin.site.register(HkuMetadataResource, HttpResourceAdmin)
admin.site.register(GreeniOAIPMHResource, HttpResourceAdmin)
admin.site.register(BuasPureResource, HttpResourceAdmin)
admin.site.register(HanzeResearchObjectResource, HttpResourceAdmin)
admin.site.register(PublinovaMetadataResource, HttpResourceAdmin)
admin.site.register(EdurepJsonSearchResource, HttpResourceAdmin)
admin.site.register(SaxionOAIPMHResource, HttpResourceAdmin)
admin.site.register(EdurepOAIPMH, HttpResourceAdmin)
admin.site.register(AnatomyToolOAIPMH, HttpResourceAdmin)

admin.site.register(HarvestSource, HarvestSourceAdmin)
admin.site.register(HarvestEntity, HarvestEntityAdmin)
