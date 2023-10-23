from django.contrib import admin

from datagrowth.admin import HttpResourceAdmin
from sources.models import (HanOAIPMHResource, HvaPureResource, HkuMetadataResource, GreeniOAIPMHResource,
                            BuasPureResource, HanzeResearchObjectResource, PublinovaMetadataResource,
                            EdurepJsonSearchResource, SaxionOAIPMHResource, EdurepOAIPMH)
from sources.models.harvest import HarvestSource, HarvestEntity


class HarvestSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "module", "is_repository",)


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

admin.site.register(HarvestSource, HarvestSourceAdmin)
admin.site.register(HarvestEntity, HarvestEntityAdmin)
