from django.conf import settings
from django.contrib import admin
from django import forms
from django.urls import reverse
from django.utils.html import format_html

from core.loading import load_harvest_models
from core.admin.widgets import PrettyJSONWidget
from testing.models import TestProduct, TestFile


class ManualDocumentAdminForm(forms.ModelForm):
    class Meta:
        model = None  # set dynamically
        fields = "__all__"
        widgets = {
            "properties": PrettyJSONWidget(attrs={"rows": 20, "cols": 80}),
        }


class ManualDocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "document_link", "created_at", "modified_at"]
    form = ManualDocumentAdminForm

    def document_link(self, obj):
        object_id = obj.properties.get("external_id", None)
        if not object_id:
            return "(not set)"
        models = load_harvest_models(obj.entity.type)
        document_list_url = reverse(f"admin:{obj.entity.type}_{models["Document"]._meta.model_name}_changelist")
        document_list_url += f"?q={object_id}&dataset_version__is_current__exact=1"
        return format_html('<a style="text-decoration: underline" href="{}">document</a>', document_list_url)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.Meta.model = self.model
        return form

    def get_readonly_fields(self, request, obj=None):
        if obj:  # When obj is not None, we are editing an existing object
            return self.readonly_fields
        else:  # When obj is None, we are adding a new object
            return self.readonly_fields + ('properties',)


if settings.ALLOW_MANUAL_DOCUMENTS:
    admin.site.register(TestProduct, ManualDocumentAdmin)
    admin.site.register(TestFile, ManualDocumentAdmin)
