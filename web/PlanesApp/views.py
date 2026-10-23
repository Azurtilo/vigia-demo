from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import ListView

from .forms import CheckoutForm, ConfirmationForm, PaymentMethodForm
from .models import Plan, SimulatedOperation, SimulatedPaymentMethod
from .permissions import ClientMixin, verified
from .services import add_method, execute, proposal, remove_method, set_default, summary
from .simulator import ERRORS


def operation_error(form, error):
    if isinstance(error, ValidationError):
        form.add_error(None, error)
    else:
        form.add_error(
            None,
            "No pudimos guardar la operación. No se confirmó ningún cambio. Inténtalo otra vez.",
        )


@method_decorator(never_cache, name="dispatch")
class CatalogView(View):
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        state = (
            summary(request.user)
            if request.user.is_authenticated and request.user.is_active
            else None
        )
        return render(
            request,
            "pages/PlanesApp/catalogo.html",
            {
                "plans": Plan.objects.filter(active=True).prefetch_related("benefits"),
                "current_plan": (
                    state["plan"] if state and state["state"] != "Vencida" else None
                ),
                "catalog_base": (
                    "components/Layout/base_extendido.html"
                    if request.user.is_authenticated
                    else "components/Layout/base.html"
                ),
            },
        )


@method_decorator(never_cache, name="dispatch")
class SummaryView(ClientMixin, View):
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        state = summary(request.user)
        return render(
            request,
            "pages/PlanesApp/mi_suscripcion.html",
            {
                **state,
                "email_verified": verified(request.user),
                "method": SimulatedPaymentMethod.objects.filter(
                    user=request.user, active=True, default=True
                ).first(),
                "resume_form": (
                    ConfirmationForm(
                        initial={
                            "token": proposal(
                                request.user, state["subscription"].plan, "resume"
                            )
                        }
                    )
                    if state["can_resume"]
                    else None
                ),
            },
        )


@method_decorator(
    [never_cache, sensitive_post_parameters("number", "cvc")], name="dispatch"
)
class MethodsView(ClientMixin, View):
    require_verified = True

    def render_form(self, request, form):
        return render(
            request,
            "pages/PlanesApp/metodos.html",
            {
                "form": form,
                "methods": SimulatedPaymentMethod.objects.filter(
                    user=request.user, active=True
                ),
            },
        )

    def get(self, request):
        return self.render_form(request, PaymentMethodForm())

    def post(self, request):
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            try:
                add_method(request.user, form.cleaned_data)
            except (ValidationError, DatabaseError) as error:
                operation_error(form, error)
            else:
                messages.success(request, "Tarjeta de prueba guardada.")
                return redirect("PlanesApp:metodos")
        return self.render_form(request, form)


class DefaultMethodView(ClientMixin, View):
    require_verified = True
    http_method_names = ["post", "options"]

    def post(self, request, pk):
        method = get_object_or_404(
            SimulatedPaymentMethod, user=request.user, pk=pk, active=True
        )
        try:
            set_default(request.user, method)
        except (ValidationError, DatabaseError) as error:
            messages.error(
                request,
                (
                    error.messages[0]
                    if isinstance(error, ValidationError)
                    else "No se pudo cambiar la tarjeta predeterminada."
                ),
            )
        else:
            messages.success(request, "Tarjeta predeterminada actualizada.")
        return redirect("PlanesApp:metodos")


@method_decorator(never_cache, name="dispatch")
class DeleteMethodView(ClientMixin, View):
    require_verified = True

    def get(self, request, pk):
        method = get_object_or_404(
            SimulatedPaymentMethod, user=request.user, pk=pk, active=True
        )
        state = summary(request.user)
        needs_cancel = bool(
            state["subscription"]
            and state["subscription"].amount_clp
            and not state["subscription"].cancel_at_period_end
            and not SimulatedPaymentMethod.objects.filter(
                user=request.user, active=True
            )
            .exclude(pk=pk)
            .exists()
        )
        token = (
            proposal(request.user, state["subscription"].plan, "cancel")
            if needs_cancel
            else ""
        )
        return render(
            request,
            "pages/PlanesApp/eliminar.html",
            {
                "method": method,
                "needs_cancel": needs_cancel,
                "token": token,
                "form": ConfirmationForm(
                    user=request.user,
                    target_limit=1 if needs_cancel else None,
                    initial={"token": token},
                ),
            },
        )

    def post(self, request, pk):
        method = get_object_or_404(
            SimulatedPaymentMethod, user=request.user, pk=pk, active=True
        )
        try:
            remove_method(
                request.user,
                method,
                request.POST.get("token"),
                request.POST.getlist("patients"),
            )
        except (ValidationError, DatabaseError) as error:
            messages.error(
                request,
                (
                    error.messages[0]
                    if isinstance(error, ValidationError)
                    else "No se pudo retirar la tarjeta."
                ),
            )
            return redirect("PlanesApp:metodo_eliminar", pk=pk)
        messages.success(request, "Tarjeta de prueba retirada.")
        return redirect("PlanesApp:metodos")


@method_decorator(never_cache, name="dispatch")
class CheckoutView(ClientMixin, View):
    require_verified = True
    kind = "purchase"

    def get_plan(self, request, code=None):
        if self.kind == "renew":
            state = summary(request.user)
            if not state["can_renew"]:
                return None
            return state["subscription"].plan
        return get_object_or_404(Plan, code=code, active=True)

    def render_form(self, request, plan, form):
        return render(
            request,
            "pages/PlanesApp/checkout.html",
            {
                **summary(request.user),
                "plan": plan,
                "form": form,
                "renew": self.kind == "renew",
            },
        )

    def get(self, request, code=None):
        plan = self.get_plan(request, code)
        if not plan:
            messages.info(
                request,
                "La renovación estará disponible al vencer tu período, si no está cancelado.",
            )
            return redirect("PlanesApp:mi_suscripcion")
        method = SimulatedPaymentMethod.objects.filter(
            user=request.user, active=True, default=True
        ).first()
        form = CheckoutForm(
            user=request.user,
            paid=bool(plan.amount_clp),
            target_limit=plan.max_active_patients,
            initial={
                "token": proposal(request.user, plan, self.kind, method),
                "method": method,
            },
        )
        return self.render_form(request, plan, form)

    def post(self, request, code=None):
        # The signed proposal identifies the renewal plan even after its first POST.
        if self.kind == "renew":
            from .services import read_proposal

            try:
                plan = get_object_or_404(
                    Plan,
                    pk=read_proposal(request.POST.get("token", ""), request.user)[
                        "plan"
                    ],
                )
            except ValidationError:
                messages.error(
                    request, "La revisión no es válida. Revisa tu suscripción."
                )
                return redirect("PlanesApp:mi_suscripcion")
        else:
            plan = get_object_or_404(Plan, code=code, active=True)
        form = CheckoutForm(
            request.POST,
            user=request.user,
            paid=bool(plan.amount_clp),
            target_limit=plan.max_active_patients,
        )
        if form.is_valid():
            try:
                method = form.cleaned_data["method"]
                operation = execute(
                    request.user,
                    form.cleaned_data["token"],
                    self.kind,
                    plan,
                    method.pk if method else None,
                    selected_patients=list(
                        form.cleaned_data["patients"].values_list("pk", flat=True)
                    ),
                )
            except (ValidationError, DatabaseError) as error:
                operation_error(form, error)
            else:
                return redirect("PlanesApp:resultado", reference=operation.reference)
        return self.render_form(request, plan, form)


class RenewView(CheckoutView):
    kind = "renew"


@method_decorator(never_cache, name="dispatch")
class CancelView(ClientMixin, View):
    kind = "cancel"

    def get(self, request):
        state = summary(request.user)
        sub = state["subscription"]
        if not sub or not state["is_paid"] or state["can_renew"]:
            return redirect("PlanesApp:mi_suscripcion")
        return render(
            request,
            "pages/PlanesApp/cancelacion.html",
            {
                **state,
                "form": ConfirmationForm(
                    user=request.user,
                    target_limit=1,
                    initial={"token": proposal(request.user, sub.plan, self.kind)},
                ),
            },
        )

    def post(self, request):
        form = ConfirmationForm(
            request.POST,
            user=request.user,
            target_limit=1 if self.kind == "cancel" else None,
        )
        if form.is_valid():
            try:
                operation = execute(
                    request.user,
                    form.cleaned_data["token"],
                    self.kind,
                    selected_patients=list(
                        form.cleaned_data["patients"].values_list("pk", flat=True)
                    ),
                )
            except (ValidationError, DatabaseError) as error:
                operation_error(form, error)
            else:
                return redirect("PlanesApp:resultado", reference=operation.reference)
        return render(
            request,
            "pages/PlanesApp/cancelacion.html",
            {**summary(request.user), "form": form},
        )


class ResumeView(CancelView):
    kind = "resume"
    http_method_names = ["post", "options"]


@method_decorator(never_cache, name="dispatch")
class ResultView(ClientMixin, View):
    http_method_names = ["get", "head", "options"]

    def get(self, request, reference):
        operation = get_object_or_404(
            SimulatedOperation, user=request.user, reference=reference
        )
        return render(
            request,
            "pages/PlanesApp/resultado.html",
            {
                "operation": operation,
                "error_message": ERRORS.get(operation.error_code, ""),
            },
        )


@method_decorator(never_cache, name="dispatch")
class HistoryView(ClientMixin, ListView):
    model = SimulatedOperation
    template_name = "pages/PlanesApp/historial.html"
    context_object_name = "operations"
    paginate_by = 10

    def get_queryset(self):
        return SimulatedOperation.objects.filter(user=self.request.user)
