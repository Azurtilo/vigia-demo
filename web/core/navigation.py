"""Spec 018 (D-080): a marked form submission replaces its browser history entry.

`static/js/historial.js` sends forms marked `data-replace-history` with the
header below. An internal redirect then comes back as JSON so the browser can
`location.replace()` it instead of pushing one more entry. Anything else (a form
with errors, a CSRF failure, an external redirect) passes through unchanged.
"""

from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme

HEADER = "HTTP_X_VIGIA_NAVIGATION"
REDIRECTS = {301, 302, 303, 307, 308}


class ReplaceNavigationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            request.method != "POST"
            or request.META.get(HEADER) != "replace"
            or response.status_code not in REDIRECTS
        ):
            return response
        location = response["Location"]
        if not url_has_allowed_host_and_scheme(
            location, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return response
        replaced = JsonResponse({"location": location})
        replaced.cookies = response.cookies  # session and pending messages
        replaced["Cache-Control"] = "no-store"
        return replaced
