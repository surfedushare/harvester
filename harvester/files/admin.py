from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from core.admin.datatypes import DatasetAdmin, DatasetVersionAdmin, SetAdmin, DocumentAdmin
from core.admin.resources import HarvesterHttpResourcesAdmin, HarvesterShellResourceAdmin
from core.admin.harvest import HarvestStateAdmin
from files.models import (Dataset, DatasetVersion, Set, FileDocument, HarvestState,
                          HttpTikaResource, ExtructResource, YoutubeThumbnailResource, PdfThumbnailResource,
                          YoutubeAPIResource, CheckURLResource)


class FileDocumentAdmin(DocumentAdmin):
    list_display = DocumentAdmin.list_display + \
        ("product_link", "is_not_found", "is_analysis_allowed", "redirects",)
    list_filter = DocumentAdmin.list_filter + ("type", "mime_type", "is_not_found", "is_analysis_allowed", "redirects",)
    readonly_fields = DocumentAdmin.readonly_fields + ("is_analysis_allowed",)

    def product_link(self, obj):
        product_id = obj.properties.get("product_id", None)
        if not product_id:
            return "(not set)"
        product_list_url = reverse("admin:products_productdocument_changelist")
        product_list_url += f"?q={product_id}&dataset_version__is_current__exact=1"
        return format_html('<a style="text-decoration: underline" href="{}">product</a>', product_list_url)


admin.site.register(Dataset, DatasetAdmin)
admin.site.register(DatasetVersion, DatasetVersionAdmin)
admin.site.register(Set, SetAdmin)
admin.site.register(FileDocument, FileDocumentAdmin)

admin.site.register(HarvestState, HarvestStateAdmin)

admin.site.register(HttpTikaResource, HarvesterHttpResourcesAdmin)
admin.site.register(ExtructResource, HarvesterHttpResourcesAdmin)
admin.site.register(YoutubeThumbnailResource, HarvesterShellResourceAdmin)
admin.site.register(PdfThumbnailResource, HarvesterHttpResourcesAdmin)
admin.site.register(YoutubeAPIResource, HarvesterHttpResourcesAdmin)
admin.site.register(CheckURLResource, HarvesterHttpResourcesAdmin)
