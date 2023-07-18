from django.contrib import admin


class ElasticIndexAdmin(admin.ModelAdmin):
    list_display = ("name", "remote_name", "remote_exists", "error_count", "language", "site", "created_at",
                    "modified_at", "pushed_at")
    list_per_page = 10
