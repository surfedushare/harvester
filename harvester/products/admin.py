from django.contrib import admin

from datagrowth.admin import DocumentAdmin as OverwriteAdmin
from core.admin.datatypes import DatasetAdmin, DatasetVersionAdmin, SetAdmin, DocumentAdmin
from core.admin.harvest import HarvestStateAdmin
from products.models import Dataset, DatasetVersion, Set, ProductDocument, HarvestState, Overwrite


admin.site.register(Dataset, DatasetAdmin)
admin.site.register(DatasetVersion, DatasetVersionAdmin)
admin.site.register(Set, SetAdmin)
admin.site.register(ProductDocument, DocumentAdmin)
admin.site.register(Overwrite, OverwriteAdmin)

admin.site.register(HarvestState, HarvestStateAdmin)
