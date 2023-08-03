from django.contrib import admin

from datagrowth.admin import HttpResourceAdmin

from core.models import (Dataset, DatasetVersion, Collection, Document, HarvestSource, HttpTikaResource, ElasticIndex,
                         ExtructResource, Query, Extension, MatomoVisitsResource)
from core.admin.datatypes import DatasetAdmin, DatasetVersionAdmin, DocumentAdmin, ExtensionAdmin, CollectionAdmin
from core.admin.harvest import HarvestSourceAdmin
from core.admin.search import ElasticIndexAdmin
from core.admin.query import QueryAdmin


admin.site.register(HarvestSource, HarvestSourceAdmin)
admin.site.register(HttpTikaResource, HttpResourceAdmin)
admin.site.register(Dataset, DatasetAdmin)
admin.site.register(DatasetVersion, DatasetVersionAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(ElasticIndex, ElasticIndexAdmin)
admin.site.register(ExtructResource, HttpResourceAdmin)
admin.site.register(MatomoVisitsResource, HttpResourceAdmin)
admin.site.register(Extension, ExtensionAdmin)
admin.site.register(Query, QueryAdmin)
