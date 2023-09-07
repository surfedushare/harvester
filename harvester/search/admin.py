from django.contrib import admin

from search.models import OpenSearchIndex


class OpenSearchIndexAdmin(admin.ModelAdmin):
    list_display = ("name", "pushed_at", "error_count",)
    list_per_page = 10
    readonly_fields = ("created_at", "modified_at",)


admin.site.register(OpenSearchIndex, OpenSearchIndexAdmin)
