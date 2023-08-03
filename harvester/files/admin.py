from django.contrib import admin

from datagrowth.admin import HttpResourceAdmin, ShellResourceAdmin

from files.models import YoutubeThumbnailResource, PdfThumbnailResource


admin.site.register(YoutubeThumbnailResource, ShellResourceAdmin)
admin.site.register(PdfThumbnailResource, HttpResourceAdmin)
