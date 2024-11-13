from django.contrib import admin

from datagrowth.resources.admin import HttpResourceAdmin
from core.admin.datatypes import DatasetAdmin, DatasetVersionAdmin, SetAdmin, DocumentAdmin
from core.admin.harvest import HarvestStateAdmin

from organizations.models import (Dataset, DatasetVersion, Set, OrganizationDocument, HarvestState,
                                  SharekitOrganizationResource, HanzeOrganizationResource)


admin.site.register(Dataset, DatasetAdmin)
admin.site.register(DatasetVersion, DatasetVersionAdmin)
admin.site.register(Set, SetAdmin)
admin.site.register(OrganizationDocument, DocumentAdmin)

admin.site.register(HarvestState, HarvestStateAdmin)

admin.site.register(SharekitOrganizationResource, HttpResourceAdmin)
admin.site.register(HanzeOrganizationResource, HttpResourceAdmin)
