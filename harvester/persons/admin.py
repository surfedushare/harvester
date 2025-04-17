from django.contrib import admin

from datagrowth.resources.admin import HttpResourceAdmin
from core.admin.datatypes import DatasetAdmin, DatasetVersionAdmin, SetAdmin, DocumentAdmin
from core.admin.harvest import HarvestStateAdmin

from persons.models import (Dataset, DatasetVersion, Set, PersonDocument, HarvestState, HkuPersonResource,
                            PublinovaPersonResource)


admin.site.register(Dataset, DatasetAdmin)
admin.site.register(DatasetVersion, DatasetVersionAdmin)
admin.site.register(Set, SetAdmin)
admin.site.register(PersonDocument, DocumentAdmin)

admin.site.register(HarvestState, HarvestStateAdmin)

admin.site.register(HkuPersonResource, HttpResourceAdmin)
admin.site.register(PublinovaPersonResource, HttpResourceAdmin)
