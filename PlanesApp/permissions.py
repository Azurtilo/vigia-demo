from allauth.account.models import EmailAddress
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render


def verified(user):
    return EmailAddress.objects.filter(user=user, verified=True).exists()


class ClientMixin(LoginRequiredMixin):
    require_verified = False

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_active:
            raise PermissionDenied
        if self.require_verified and not verified(request.user):
            return render(request, "pages/PlanesApp/verificar.html", status=403)
        return super().dispatch(request, *args, **kwargs)
