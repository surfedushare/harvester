from django.contrib import admin

from core.admin.datatypes import DatasetAdmin, DatasetVersionAdmin, SetAdmin, DocumentAdmin
from core.admin.harvest import HarvestStateAdmin

from organizations.models import Dataset, DatasetVersion, Set, OrganizationDocument, HarvestState


admin.site.register(Dataset, DatasetAdmin)
admin.site.register(DatasetVersion, DatasetVersionAdmin)
admin.site.register(Set, SetAdmin)
admin.site.register(OrganizationDocument, DocumentAdmin)

admin.site.register(HarvestState, HarvestStateAdmin)
