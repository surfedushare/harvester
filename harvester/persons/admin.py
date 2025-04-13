from django.contrib import admin

from core.admin.datatypes import DatasetAdmin, DatasetVersionAdmin, SetAdmin, DocumentAdmin
from core.admin.harvest import HarvestStateAdmin

from persons.models import (Dataset, DatasetVersion, Set, PersonDocument, HarvestState)


admin.site.register(Dataset, DatasetAdmin)
admin.site.register(DatasetVersion, DatasetVersionAdmin)
admin.site.register(Set, SetAdmin)
admin.site.register(PersonDocument, DocumentAdmin)

admin.site.register(HarvestState, HarvestStateAdmin)
