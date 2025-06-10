from django.contrib import admin

from core.models import Query
from core.admin.query import QueryAdmin


admin.site.register(Query, QueryAdmin)
