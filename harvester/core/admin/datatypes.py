from opensearchpy import NotFoundError

from django.contrib import admin
from django.contrib import messages

from admin_confirm import AdminConfirmMixin
from admin_confirm.admin import confirm_action
from datagrowth.admin import DataStorageAdmin, DocumentAdmin as DatagrowthDocumentAdmin

from search.clients import get_opensearch_client


class DatasetAdmin(DataStorageAdmin):
    list_display = ('__str__', 'is_harvested', 'indexing',)


class DatasetVersionAdmin(AdminConfirmMixin, admin.ModelAdmin):

    list_display = ('__str__', 'is_current', "is_index_promoted", "created_at", "harvest_count", "index_count",)
    list_per_page = 10
    actions = ["promote_dataset_version_index"]
    readonly_fields = ("is_current", "is_index_promoted",)

    def harvest_count(self, obj):
        return obj.documents.filter(properties__state="active", dataset_version=obj).count()

    def index_count(self, obj):
        if not obj.index:
            return 0
        es_client = get_opensearch_client()
        indices = obj.index.get_remote_names()
        try:
            counts = es_client.count(index=",".join(indices))
        except NotFoundError:
            counts = {}
        return counts.get("count", 0)

    @confirm_action
    def promote_dataset_version_index(self, request, queryset):
        if queryset.count() > 1:
            messages.error(request, "Can't promote more than one dataset version at a time")
            return
        # TODO: implement how exactly?
        # dataset_version = queryset.first()
        # promote_dataset_version.delay(dataset_version.id)
        messages.info(request, "A job to switch the dataset version has been dispatched. "
                               "Please refresh the page in a couple of minutes to see the results.")


class DocumentAdmin(DatagrowthDocumentAdmin):
    list_display = ('identity', 'state', 'modified_at',)
    list_per_page = 10
    list_filter = ('dataset_version__is_current', 'collection__name', 'state',)
    readonly_fields = ("created_at", "modified_at",)

    def changelist_view(self, request, extra_context=None):
        # Filter on current dataset version if no filter is being used
        if not request.GET and "?" not in request.META['REQUEST_URI']:
            parameters = request.GET.copy()
            parameters["dataset_version__is_current__exact"] = "1"
            request.GET = parameters
            request.META['QUERY_STRING'] = request.GET.urlencode()
        return super().changelist_view(request, extra_context=extra_context)


class SetAdmin(DataStorageAdmin):
    list_display = [
        '__str__', 'created_at', 'modified_at',
        'active_document_count', 'deleted_document_count', 'inactive_document_count'
    ]
    list_filter = ('dataset_version__is_current',)
    ordering = ('-created_at',)
    list_per_page = 10

    def changelist_view(self, request, extra_context=None):
        # Filter on current dataset version if no filter is being used
        if not request.GET and "?" not in request.META['REQUEST_URI']:
            parameters = request.GET.copy()
            parameters["dataset_version__is_current__exact"] = "1"
            request.GET = parameters
            request.META['QUERY_STRING'] = request.GET.urlencode()
        return super().changelist_view(request, extra_context=extra_context)

    def active_document_count(self, obj):
        return obj.documents.filter(properties__state="active").count()

    def deleted_document_count(self, obj):
        return obj.documents.filter(properties__state="deleted").count()

    def inactive_document_count(self, obj):
        return obj.documents.filter(properties__state="inactive").count()
