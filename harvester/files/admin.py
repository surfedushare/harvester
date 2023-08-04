from django.contrib import admin

from datagrowth.admin import HttpResourceAdmin, ShellResourceAdmin

from files.models import HttpTikaResource, ExtructResource, YoutubeThumbnailResource, PdfThumbnailResource

admin.site.register(HttpTikaResource, HttpResourceAdmin)
admin.site.register(ExtructResource, HttpResourceAdmin)
admin.site.register(YoutubeThumbnailResource, ShellResourceAdmin)
admin.site.register(PdfThumbnailResource, HttpResourceAdmin)
