"""Web gate: an account uses the portal only after accepting the current policy."""

from urllib.parse import quote

from django.shortcuts import redirect
from django.urls import reverse

from . import consent

SESSION_KEY = "privacy_policy_version"
# Login, logout, recovery, e-mail confirmation and MFA live under /accounts/; the
# API answers consent_required itself (CuidadosApp.api.base).
EXEMPT = ("/privacidad/", "/accounts/", "/_allauth/", "/api/", "/static/", "/media/", "/mobile/")


class ConsentRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            consent.enforced()
            and user is not None
            and user.is_authenticated
            and user.is_active
            and not request.path.startswith(EXEMPT)
            and request.session.get(SESSION_KEY) != consent.version()
        ):
            if not consent.account_ok(user):
                target = reverse("PrivacidadApp:accept")
                return redirect(f"{target}?next={quote(request.get_full_path())}")
            request.session[SESSION_KEY] = consent.version()
        return self.get_response(request)
