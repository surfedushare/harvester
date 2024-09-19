from django.conf import settings
from django.contrib import admin
from rest_framework.authtoken.models import TokenProxy
from allauth.account.decorators import secure_admin_login


class HarvesterTokenAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(user=request.user)


if settings.ENABLE_SURFCONEXT_LOGIN:
    admin.site.login = secure_admin_login(admin.site.login)

admin.site.unregister(TokenProxy)
admin.site.register(TokenProxy, HarvesterTokenAdmin)
