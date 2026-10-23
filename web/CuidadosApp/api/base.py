import json

from allauth.headless.internal.sessionkit import authenticate_by_x_session_token
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt


def error(message, status=400, **extra):
    return JsonResponse({"error": message, **extra}, status=status)


@method_decorator(csrf_exempt, name="dispatch")
class MobileView(View):
    """Header-only authentication: browser cookies never authorize this API."""

    http_method_names = ["get", "post", "delete", "options"]

    def dispatch(self, request, *args, **kwargs):
        token = request.headers.get("X-Session-Token", "")
        auth = (
            authenticate_by_x_session_token(token)
            if token and len(token) <= 128
            else None
        )
        if not auth or not auth[0].is_active:
            response = error("Tu sesión terminó. Vuelve a ingresar.", 401)
        else:
            request.user = auth[0]
            try:
                if request.method == "POST":
                    if (
                        request.content_type != "application/json"
                        or len(request.body) > 32768
                    ):
                        raise ValidationError("Envía un objeto JSON de hasta 32 KB.")
                    self.data = json.loads(request.body)
                    if not isinstance(self.data, dict):
                        raise ValidationError("El contenido debe ser un objeto JSON.")
                response = super().dispatch(request, *args, **kwargs)
            except Http404:
                response = error("No se encontró este recurso.", 404)
            except PermissionDenied:
                response = error("Esta función no está disponible para tu cuenta.", 403)
            except ValidationError as exc:
                response = error(" ".join(exc.messages))
            except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                response = error("Revisa los datos enviados.")
        response["Cache-Control"] = "no-store, private"
        response["Vary"] = "X-Session-Token"
        return response

    def validated(self, form):
        if not form.is_valid():
            raise ValidationError(
                [
                    str(message)
                    for messages in form.errors.values()
                    for message in messages
                ]
            )
        return form
