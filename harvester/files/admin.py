from django.contrib import admin
from django.utils.html import format_html, html_safe
from django.urls import reverse

from core.admin.datatypes import DatasetAdmin, DatasetVersionAdmin, SetAdmin, DocumentAdmin
from core.admin.resources import HarvesterHttpResourcesAdmin, HarvesterShellResourceAdmin
from core.admin.harvest import HarvestStateAdmin
from files.models import (Dataset, DatasetVersion, Set, FileDocument, HarvestState,
                          HttpTikaResource, ExtructResource, YoutubeThumbnailResource, PdfThumbnailResource)


class FileDocumentAdmin(DocumentAdmin):
    list_display = DocumentAdmin.list_display + \
        ("product_link", "pipeline_info", "is_not_found", "is_analysis_allowed", "is_invalid",)
    list_filter = DocumentAdmin.list_filter + ("is_not_found", "is_analysis_allowed", "is_invalid",)
    readonly_fields = DocumentAdmin.readonly_fields + ("is_not_found", "is_analysis_allowed", "is_invalid",)

    def product_link(self, obj):
        product_id = obj.properties.get("product_id", None)
        if not product_id:
            return "(not set)"
        product_list_url = reverse("admin:products_productdocument_changelist")
        product_list_url += f"?q={product_id}&dataset_version__is_current__exact=1"
        return format_html('<a href="{}">product</a>', product_list_url)

    def pipeline_info(self, obj):
        if not obj.pipeline:
            return "(no pipeline tasks)"
        tasks_html = []
        for task_name, task_info in obj.pipeline.items():
            if "resource" in task_info:
                resource_url_name = task_info["resource"].replace(".", "_").lower()
                resource_change_url = reverse(f"admin:{resource_url_name}_change", args=(task_info["id"],))
                color = "green" if task_info["success"] else "red"
                task_html = format_html(
                    '<a style="color:{}" href="{}">{}</a>', color, resource_change_url, task_name
                )
            else:
                color = "green" if task_info["success"] else "red"
                task_html = format_html('<span style="color:{}">{}</span>', color, task_name)
            tasks_html.append(task_html)
        return format_html(", ".join(tasks_html))


admin.site.register(Dataset, DatasetAdmin)
admin.site.register(DatasetVersion, DatasetVersionAdmin)
admin.site.register(Set, SetAdmin)
admin.site.register(FileDocument, FileDocumentAdmin)

admin.site.register(HarvestState, HarvestStateAdmin)

admin.site.register(HttpTikaResource, HarvesterHttpResourcesAdmin)
admin.site.register(ExtructResource, HarvesterHttpResourcesAdmin)
admin.site.register(YoutubeThumbnailResource, HarvesterShellResourceAdmin)
admin.site.register(PdfThumbnailResource, HarvesterHttpResourcesAdmin)
