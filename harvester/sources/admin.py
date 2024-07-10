from django.conf import settings
from django.contrib import admin, messages
from django.utils.timezone import now
from django.utils.html import format_html
from django.urls import reverse

from datagrowth.admin import HttpResourceAdmin
from core.loading import load_harvest_models
from sources.models import (HvaPureResource, HkuMetadataResource, GreeniOAIPMHResource, BuasPureResource,
                            HanzeResearchObjectResource, PublinovaMetadataResource, SharekitMetadataHarvest,
                            SaxionOAIPMHResource, AnatomyToolOAIPMH, EdurepOAIPMH)
from sources.models.harvest import HarvestSource, HarvestEntity


class HarvestSourceAdmin(admin.ModelAdmin):

    list_display = ("name", "module", "is_repository", "show_entities")
    actions = ["purge_source_harvest_states", "set_source_to_manual_harvest", "set_source_to_automatic_harvest"]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not settings.ALLOW_MANUAL_DOCUMENTS:
            for manual_action in ["set_source_to_manual_harvest", "set_source_to_automatic_harvest"]:
                actions.pop(manual_action)
        return actions

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

    def set_source_to_manual_harvest(self, request, queryset):
        update_count = HarvestEntity.objects.filter(source__in=queryset).update(is_manual=True)
        messages.info(request, f"Set {update_count} entities to manual mode")

    def set_source_to_automatic_harvest(self, request, queryset):
        update_count = HarvestEntity.objects.filter(source__in=queryset).update(is_manual=False)
        messages.info(request, f"Set {update_count} entities to auto mode")

    def show_entities(self, obj):
        if not obj.id:
            return "(unknown)"
        entity_list_url = reverse("admin:sources_harvestentity_changelist")
        entity_list_url += f"?source__id__exact={obj.id}"
        return format_html('<a style="text-decoration: underline" href="{}">entities</a>', entity_list_url)


class HarvestEntityAdmin(admin.ModelAdmin):
    list_display = ("source", "type", "is_available", "is_manual")
    list_filter = ("source", "type",)


admin.site.register(HvaPureResource, HttpResourceAdmin)
admin.site.register(HkuMetadataResource, HttpResourceAdmin)
admin.site.register(GreeniOAIPMHResource, HttpResourceAdmin)
admin.site.register(BuasPureResource, HttpResourceAdmin)
admin.site.register(HanzeResearchObjectResource, HttpResourceAdmin)
admin.site.register(PublinovaMetadataResource, HttpResourceAdmin)
admin.site.register(SharekitMetadataHarvest, HttpResourceAdmin)
admin.site.register(SaxionOAIPMHResource, HttpResourceAdmin)
admin.site.register(EdurepOAIPMH, HttpResourceAdmin)
admin.site.register(AnatomyToolOAIPMH, HttpResourceAdmin)

admin.site.register(HarvestSource, HarvestSourceAdmin)
admin.site.register(HarvestEntity, HarvestEntityAdmin)
