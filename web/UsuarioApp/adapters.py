from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.db import transaction

from .services import provision_public_user


class NoSignupAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False


class PublicAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return not request.user.is_authenticated

    @transaction.atomic
    def save_user(self, request, user, form, commit=True):
        new = user.pk is None
        if new:
            user.is_staff = user.is_superuser = False
        user = super().save_user(request, user, form, commit=commit)
        if new and commit:
            provision_public_user(user)
        return user


class PublicSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return (
            sociallogin.account.provider == "google"
            and not request.user.is_authenticated
        )

    @transaction.atomic
    def save_user(self, request, sociallogin, form=None):
        sociallogin.user.is_staff = sociallogin.user.is_superuser = False
        user = super().save_user(request, sociallogin, form)
        provision_public_user(user)
        return user
