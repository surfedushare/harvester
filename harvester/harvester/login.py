from django.conf import settings
from django.contrib.auth.models import Group, User

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from rest_framework.authtoken.models import Token


class HarvesterSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        # If a user already exists with the incoming email address it should just be logged in.
        email = sociallogin.account.extra_data.get("email")
        if email:
            try:
                user = User.objects.get(username=email)
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass

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
