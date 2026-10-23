from allauth.account.forms import SignupForm
from django.db import transaction


class PublicSignupForm(SignupForm):
    @transaction.atomic
    def save(self, request):
        # Wrap allauth's EmailAddress and custom_signup too, not only User.save.
        return super().save(request)
