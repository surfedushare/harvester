from django.contrib import admin

from datagrowth.admin import HttpResourceAdmin
from sources.models import HanOAIPMHResource, HvaPureResource


admin.site.register(HanOAIPMHResource, HttpResourceAdmin)
admin.site.register(HvaPureResource, HttpResourceAdmin)
