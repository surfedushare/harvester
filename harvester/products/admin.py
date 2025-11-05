from django.contrib import admin

from core.admin.datatypes import DatasetAdmin, DatasetVersionAdmin, SetAdmin, DocumentAdmin, OverwriteAdmin
from core.admin.harvest import HarvestStateAdmin
from core.admin.filters import HasMaterialListFilter
from products.models import Dataset, DatasetVersion, Set, ProductDocument, HarvestState, Overwrite


class ProductDocumentAdmin(DocumentAdmin):
    list_filter = DocumentAdmin.list_filter + (HasMaterialListFilter,)


admin.site.register(Dataset, DatasetAdmin)
admin.site.register(DatasetVersion, DatasetVersionAdmin)
admin.site.register(Set, SetAdmin)
admin.site.register(ProductDocument, ProductDocumentAdmin)
admin.site.register(Overwrite, OverwriteAdmin)

admin.site.register(HarvestState, HarvestStateAdmin)
