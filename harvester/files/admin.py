from django.contrib import admin

from core.admin.datatypes import DatasetAdmin, DatasetVersionAdmin, SetAdmin, DocumentAdmin
from core.admin.resources import HarvesterHttpResourcesAdmin, HarvesterShellResourceAdmin
from core.admin.harvest import HarvestStateAdmin
from files.models import (Dataset, DatasetVersion, Set, FileDocument, HarvestState,
                          HttpTikaResource, ExtructResource, YoutubeThumbnailResource, PdfThumbnailResource)


class FileDocumentAdmin(DocumentAdmin):
    list_display = DocumentAdmin.list_display + ("type", "is_not_found", "is_analysis_allowed",)
    list_filter = DocumentAdmin.list_filter + ("type", "mime_type", "is_not_found", "is_analysis_allowed",)


admin.site.register(Dataset, DatasetAdmin)
admin.site.register(DatasetVersion, DatasetVersionAdmin)
admin.site.register(Set, SetAdmin)
admin.site.register(FileDocument, FileDocumentAdmin)

admin.site.register(HarvestState, HarvestStateAdmin)

admin.site.register(HttpTikaResource, HarvesterHttpResourcesAdmin)
admin.site.register(ExtructResource, HarvesterHttpResourcesAdmin)
admin.site.register(YoutubeThumbnailResource, HarvesterShellResourceAdmin)
admin.site.register(PdfThumbnailResource, HarvesterHttpResourcesAdmin)
