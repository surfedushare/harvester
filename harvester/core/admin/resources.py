from datagrowth.admin import HttpResourceAdmin, ShellResourceAdmin


class HarvesterHttpResourcesAdmin(HttpResourceAdmin):
    list_display = ("__str__", "uri", "status", "created_at", "modified_at",)
    list_filter = ("status",)


class HarvesterShellResourceAdmin(ShellResourceAdmin):
    list_display = ("__str__", "uri", "status", "stderr", "created_at", "modified_at",)
    list_filter = ("status",)
