from django.conf import settings
from django.contrib.auth.models import Group

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from rest_framework.authtoken.models import Token


class HarvesterSocialAccountAdapter(DefaultSocialAccountAdapter):

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.username = user.email
        user.is_staff = True
        user.is_superuser = False
        if sociallogin.account and sociallogin.account.extra_data:
            for role in sociallogin.account.extra_data.get("edumember_is_member_of", []):
                if role in settings.CONEXT_SUPERUSER_MEMBERS:
                    user.is_superuser = True
                    break
        return user

    def save_user(self, request, sociallogin, form=None):
        saved_user = super().save_user(request, sociallogin, form)
        group = Group.objects.get(name=settings.CONEXT_DEFAULT_GROUP)
        saved_user.groups.add(group)
        Token.objects.create(user=saved_user)
        return saved_user
