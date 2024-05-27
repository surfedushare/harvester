from django.contrib import admin

from datagrowth.admin import HttpResourceAdmin

from core.models import Query, MatomoVisitsResource
from core.admin.query import QueryAdmin


admin.site.register(MatomoVisitsResource, HttpResourceAdmin)
admin.site.register(Query, QueryAdmin)
