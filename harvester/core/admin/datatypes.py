from opensearchpy import NotFoundError

from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse

from admin_confirm import AdminConfirmMixin
from admin_confirm.admin import confirm_action
from datagrowth.admin import DataStorageAdmin, DocumentAdmin as DatagrowthDocumentAdmin

from search.clients import get_opensearch_client
from core.tasks.commands import promote_dataset_version


class HarvestObjectMixinAdmin(object):

    def pipeline_info(self, obj):
        if not obj.pipeline:
            return "(no pipeline tasks)"
        tasks_html = []
        for task_name, task_info in obj.pipeline.items():
            if "resource" in task_info:
                resource_url_name = task_info["resource"].replace(".", "_").lower()
                resource_change_url = reverse(f"admin:{resource_url_name}_change", args=(task_info["id"],))
                color = "green" if task_info["success"] else "red"
                task_html = format_html(
                    '<a style="color:{}; text-decoration: underline" href="{}">{}</a>',
                    color, resource_change_url, task_name
                )
            else:
                color = "green" if task_info["success"] else "red"
                task_html = format_html('<span style="color:{}">{}</span>', color, task_name)
            tasks_html.append(task_html)
        return format_html(", ".join(tasks_html))


class DatasetAdmin(DataStorageAdmin):
    list_display = ('__str__', 'is_harvested', 'indexing',)


class DatasetVersionAdmin(AdminConfirmMixin, HarvestObjectMixinAdmin, admin.ModelAdmin):

    list_display = ('__str__', "pipeline_info", "created_at", "pending_at", 'is_current', "is_index_promoted",
                    "harvest_count", "index_count",)
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
        dataset_version = queryset.first()
        promote_dataset_version.delay(dataset_version.id, dataset_version._meta.app_label)
        messages.info(request, "A job to switch the dataset version has been dispatched. "
                               "Please refresh the page in a couple of minutes to see the results.")


class DocumentAdmin(HarvestObjectMixinAdmin, DatagrowthDocumentAdmin):
    list_display = ('identity', 'state', 'pipeline_info', 'modified_at', "pending_at",)
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


class SetAdmin(HarvestObjectMixinAdmin, DataStorageAdmin):
    list_display = [
        '__str__', 'pipeline_info', 'created_at', 'pending_at',
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
