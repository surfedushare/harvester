from django.contrib import admin

from core.admin.datatypes import DatasetAdmin, DatasetVersionAdmin, SetAdmin, DocumentAdmin
from core.admin.harvest import HarvestStateAdmin
from core.admin.resources import HarvesterHttpResourcesAdmin
from projects.models import (Dataset, DatasetVersion, Set, ProjectDocument, HarvestState, SiaProjectIdsResource,
                             SiaProjectDetailsResource, BuasPureProjectResource, HanzePureProjectResource,
                             HkuProjectResource, HuProjectResource, PublinovaProjectsResource)


admin.site.register(Dataset, DatasetAdmin)
admin.site.register(DatasetVersion, DatasetVersionAdmin)
admin.site.register(Set, SetAdmin)
admin.site.register(ProjectDocument, DocumentAdmin)

admin.site.register(HarvestState, HarvestStateAdmin)

admin.site.register(SiaProjectIdsResource, HarvesterHttpResourcesAdmin)
admin.site.register(SiaProjectDetailsResource, HarvesterHttpResourcesAdmin)
admin.site.register(BuasPureProjectResource, HarvesterHttpResourcesAdmin)
admin.site.register(HanzePureProjectResource, HarvesterHttpResourcesAdmin)
admin.site.register(HkuProjectResource, HarvesterHttpResourcesAdmin)
admin.site.register(HuProjectResource, HarvesterHttpResourcesAdmin)
admin.site.register(PublinovaProjectsResource, HarvesterHttpResourcesAdmin)
