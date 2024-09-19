from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class HarvesterSocialAccountAdapter(DefaultSocialAccountAdapter):

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.username = user.email
        user.is_staff = True
        user.is_superuser = True
        return user

    def save_user(self, request, sociallogin, form=None):
        saved_user = super().save_user(request, sociallogin, form)
        # TODO: enable below when SURFConext gives info about Invite roles.
        # group = Group.objects.get(name=STAFF_GROUP_NAME)
        # saved_user.groups.add(group)
        return saved_user
