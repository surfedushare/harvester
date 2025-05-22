from django.contrib import admin

from datagrowth.resources.admin import HttpResourceAdmin
from core.admin.datatypes import DatasetAdmin, DatasetVersionAdmin, SetAdmin, DocumentAdmin
from core.admin.harvest import HarvestStateAdmin

from persons.models import (Dataset, DatasetVersion, Set, PersonDocument, HarvestState, HkuPersonResource,
                            PublinovaPersonResource, HanzePersonResource, HanzeUserResource, HvaPersonResource,
                            HvAUserResource, HuPersonResource, BuasPersonResource)


admin.site.register(Dataset, DatasetAdmin)
admin.site.register(DatasetVersion, DatasetVersionAdmin)
admin.site.register(Set, SetAdmin)
admin.site.register(PersonDocument, DocumentAdmin)

admin.site.register(HarvestState, HarvestStateAdmin)

admin.site.register(HkuPersonResource, HttpResourceAdmin)
admin.site.register(PublinovaPersonResource, HttpResourceAdmin)
admin.site.register(HanzePersonResource, HttpResourceAdmin)
admin.site.register(HanzeUserResource, HttpResourceAdmin)
admin.site.register(HvaPersonResource, HttpResourceAdmin)
admin.site.register(HvAUserResource, HttpResourceAdmin)
admin.site.register(HuPersonResource, HttpResourceAdmin)
admin.site.register(BuasPersonResource, HttpResourceAdmin)
