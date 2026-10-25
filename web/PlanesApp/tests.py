from datetime import datetime, timedelta
from importlib import import_module
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

from allauth.account.models import EmailAddress, EmailConfirmationHMAC
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.apps import apps
from django.contrib.auth.models import AnonymousUser, User
from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, connection, transaction
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from UsuarioApp.adapters import PublicSocialAccountAdapter
from UsuarioApp.models import Position, Profile

from .admin import PlanAdminForm
from .forms import PaymentMethodForm
from .models import Plan, SimulatedOperation, SimulatedPaymentMethod, Subscription
from .services import (
    add_method,
    execute,
    month_after,
    proposal,
    remove_method,
    set_default,
    summary,
)

PASSWORD = "Demo-Planes-2026-Fuerte!"
GOOGLE_TEST = {
    "google": {
        "APP": {"client_id": "demo-only", "secret": "demo-only", "key": ""},
        "OAUTH_PKCE_ENABLED": True,
    }
}
CARD = {
    "holder": "Ana Demo",
    "number": "4242 4242 4242 4242",
    "expiry": "12/30",
    "cvc": "123",
}


class PlanesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed = import_module("PlanesApp.migrations.0002_catalogo_inicial").seed
        seed(apps, type("Schema", (), {"connection": connection})())
        cls.user = User.objects.create_user(
            "cliente_demo", email="demo@example.test", password=PASSWORD
        )
        cls.other = User.objects.create_user(
            "otro_demo", email="otro@example.test", password=PASSWORD
        )
        for user in (cls.user, cls.other):
            EmailAddress.objects.create(
                user=user, email=user.email, verified=True, primary=True
            )
            Profile.objects.create(
                user_FK=user,
                position_FK=Position.objects.get(user_position="Cliente público"),
            )

    def setUp(self):
        self.client.force_login(self.user)
        self.plus = Plan.objects.get(code="plus")
        self.pro = Plan.objects.get(code="pro")

    def card(self, number=None, user=None):
        form = PaymentMethodForm({**CARD, **({"number": number} if number else {})})
        self.assertTrue(form.is_valid(), form.errors)
        return add_method(user or self.user, form.cleaned_data)

    def buy(self, plan=None, method=None):
        plan = plan or self.plus
        method = method or self.card()
        return execute(
            self.user,
            proposal(self.user, plan, "purchase"),
            "purchase",
            plan,
            method.pk,
        )

    def test_catalogo_seed_exacto_y_anonimo(self):
        self.client.logout()
        response = self.client.get(reverse("PlanesApp:catalogo"))
        self.assertContains(response, "$4.990")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertNotContains(response, "$14.990")
        self.assertContains(response, "VIGIA Premium")
        self.assertEqual(list(Plan.objects.filter(active=True).values_list("max_active_patients", flat=True)), [1, 3, None])
        self.assertEqual(
            list(Plan.objects.values_list("amount_clp", flat=True)),
            [0, 4990, 9990, 14990],
        )
        self.assertEqual(Plan.objects.get(code="hogar").benefits.count(), 5)
        self.assertNotContains(response, "Más elegido")

    def test_get_propios_no_crea_suscripcion_perfil_operacion(self):
        before = (
            Subscription.objects.count(),
            Profile.objects.count(),
            SimulatedOperation.objects.count(),
        )
        for route in ("mi_suscripcion", "historial", "metodos"):
            self.assertEqual(
                self.client.get(reverse("PlanesApp:" + route)).status_code, 200
            )
        self.assertEqual(
            before,
            (
                Subscription.objects.count(),
                Profile.objects.count(),
                SimulatedOperation.objects.count(),
            ),
        )

    def test_alta_local_atomic_restricted_free_email_no_verificado(self):
        self.client.logout()
        response = self.client.post(
            reverse("account_signup"),
            {
                "username": "nuevo_demo",
                "email": "nuevo@example.test",
                "password1": PASSWORD,
                "password2": PASSWORD,
                "accept_privacy": "on",
                "is_staff": "1",
                "is_superuser": "1",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="nuevo_demo")
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertEqual(user.profile.position_FK.permission_code, "RESTRICTED")
        self.assertEqual(Subscription.objects.get(user=user).plan.code, "free")
        self.assertFalse(EmailAddress.objects.get(user=user).verified)
        self.assertTrue(mail.outbox)

    def test_alta_rollback_incluye_email_y_perfil(self):
        self.client.logout()
        # Failure after the profile is actually written rolls back all public records.
        with patch(
            "PlanesApp.services.ensure_subscription",
            side_effect=IntegrityError("synthetic"),
        ):
            with self.assertRaises(IntegrityError):
                self.client.post(
                    reverse("account_signup"),
                    {
                        "username": "fallo_demo",
                        "email": "fallo@example.test",
                        "password1": PASSWORD,
                        "password2": PASSWORD,
                        "accept_privacy": "on",
                    },
                )
        self.assertFalse(User.objects.filter(username="fallo_demo").exists())
        self.assertFalse(
            EmailAddress.objects.filter(email="fallo@example.test").exists()
        )

    def test_alta_duplicados_y_password_no_crean_registros(self):
        self.client.logout()
        before = User.objects.count()
        for data in (
            {"username": self.user.username, "email": "nuevo@example.test"},
            {"username": "duplicado", "email": self.user.email},
            {
                "username": "corto",
                "email": "corto@example.test",
                "password1": "12",
                "password2": "12",
            },
        ):
            response = self.client.post(
                reverse("account_signup"),
                {"password1": PASSWORD, "password2": PASSWORD, **data},
            )
            self.assertIn(response.status_code, (200, 302))
        self.assertEqual(User.objects.count(), before)

    def test_signup_autenticado_no_crea_segunda_cuenta(self):
        before = User.objects.count()
        self.client.post(
            reverse("account_signup"),
            {
                "username": "segunda",
                "email": "segunda@example.test",
                "password1": PASSWORD,
                "password2": PASSWORD,
            },
        )
        self.assertEqual(User.objects.count(), before)

    def test_confirmacion_real_y_token_invalido(self):
        address = EmailAddress.objects.get(user=self.user)
        address.verified = False
        address.save()
        key = EmailConfirmationHMAC(address).key
        self.assertEqual(self.client.get(reverse("PlanesApp:metodos")).status_code, 403)
        self.client.post(reverse("account_confirm_email", args=["invalid-token"]))
        address.refresh_from_db()
        self.assertFalse(address.verified)
        self.client.post(reverse("account_confirm_email", args=[key]))
        address.refresh_from_db()
        self.assertTrue(address.verified)
        self.assertEqual(self.client.get(reverse("PlanesApp:metodos")).status_code, 200)

    def test_email_invalido_o_expirado_y_reenvio_local(self):
        address = EmailAddress.objects.get(user=self.user)
        address.verified = False
        address.save()
        with patch("django.core.signing.time.time", return_value=0):
            key = EmailConfirmationHMAC(address).key
        self.client.post(reverse("account_confirm_email", args=[key]))
        address.refresh_from_db()
        self.assertFalse(address.verified)
        self.client.post(
            reverse("account_email"), {"email": address.email, "action_send": "1"}
        )
        self.assertTrue(mail.outbox)

    def test_metodos_y_checkout_exigen_email_en_servidor(self):
        EmailAddress.objects.filter(user=self.user).update(verified=False)
        for route in ("metodos", "renovar"):
            self.assertEqual(
                self.client.get(reverse("PlanesApp:" + route)).status_code, 403
            )
        self.assertEqual(
            self.client.post(reverse("PlanesApp:metodos"), CARD).status_code, 403
        )
        with self.assertRaises(PermissionDenied):
            execute(
                self.user,
                proposal(self.user, self.plus, "purchase"),
                "purchase",
                self.plus,
            )

    def test_matriz_lectura_interna_y_navegacion(self):
        admin = Position.objects.create(
            user_position="Administrador demo", permission_code="ADMIN"
        )
        manager = Position.objects.create(
            user_position="Gestor demo", permission_code="MANAGER"
        )
        for role, position, root, staff, expected in [
            (
                "restricted",
                Position.objects.get(user_position="Cliente público"),
                False,
                False,
                False,
            ),
            ("admin", admin, False, False, True),
            ("manager", manager, False, False, True),
            ("no-profile", None, False, False, False),
            ("staff", None, False, True, False),
            ("root", None, True, True, True),
        ]:
            with self.subTest(role=role):
                user = User.objects.create_user(
                    "actor_" + role, is_superuser=root, is_staff=staff
                )
                if position:
                    Profile.objects.create(user_FK=user, position_FK=position)
                self.client.force_login(user)
                home = self.client.get(reverse("Home"))
                self.assertEqual(home.status_code, 200 if expected else 302)
                listing = self.client.get(reverse("User"))
                self.assertEqual(listing.status_code, 200 if expected else 403)
                page = self.client.get(reverse("PlanesApp:mi_suscripcion"))
                self.assertEqual(page.status_code, 200)
                (
                    self.assertContains(page, 'href="/usuarios/"')
                    if expected
                    else self.assertNotContains(page, 'href="/usuarios/"')
                )
                self.assertEqual(
                    self.client.get(reverse("Register")).status_code,
                    200 if position in (admin, manager) else 302,
                )

    def test_home_cliente_no_consulta_cuentas(self):
        with patch(
            "homeApp.views.HomeView.get_queryset",
            side_effect=AssertionError("must not run"),
        ):
            self.assertRedirects(
                self.client.get(reverse("Home")), reverse("CuidadosApp:panel")
            )

    def test_sin_perfil_y_cargo_no_se_autoprovisionan_en_get(self):
        Profile.objects.filter(user_FK=self.user).delete()
        self.assertEqual(
            self.client.get(reverse("PlanesApp:mi_suscripcion")).status_code, 200
        )
        self.assertFalse(Profile.objects.filter(user_FK=self.user).exists())

    def test_anonimo_inactivo_y_csrf(self):
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.user)
        self.assertEqual(
            secure.post(reverse("PlanesApp:metodos"), CARD).status_code, 403
        )
        self.user.is_active = False
        self.user.save()
        self.assertEqual(
            self.client.get(reverse("PlanesApp:mi_suscripcion")).status_code, 302
        )
        self.client.logout()
        for route in ("mi_suscripcion", "metodos", "historial"):
            self.assertEqual(
                self.client.get(reverse("PlanesApp:" + route)).status_code, 302
            )

    def test_card_no_pan_cvc_y_default_unique(self):
        method = self.card()
        self.assertEqual(method.last4, "4242")
        self.assertTrue(method.default)
        self.assertNotIn("number", [f.name for f in method._meta.fields])
        self.assertNotIn("cvc", [f.name for f in method._meta.fields])
        with self.assertRaises(ValidationError):
            self.card()
        second = self.card("5555555555554444")
        set_default(self.user, second)
        self.assertEqual(
            SimulatedPaymentMethod.objects.filter(
                user=self.user, default=True, active=True
            ).count(),
            1,
        )

    def test_validacion_tarjeta_rechaza_fuera_lista_fecha_cvc_nombre(self):
        for changes in (
            {"number": "4111111111111111"},
            {"expiry": "13/30"},
            {"expiry": "01/20"},
            {"cvc": "1ab"},
            {"holder": "123456"},
        ):
            with self.subTest(changes=changes):
                self.assertFalse(PaymentMethodForm({**CARD, **changes}).is_valid())
        self.assertTrue(
            PaymentMethodForm({**CARD, "holder": "María O’Neill"}).is_valid()
        )

    def test_error_no_refleja_numero_cvc_ni_cache(self):
        response = self.client.post(
            reverse("PlanesApp:metodos"), {**CARD, "expiry": "13/30"}
        )
        self.assertNotContains(response, 'value="4242 4242 4242 4242"')
        self.assertNotContains(response, 'value="123"')
        self.assertIn("no-store", response["Cache-Control"])
        self.assertFalse(SimulatedPaymentMethod.objects.exists())

    def test_compra_precio_servidor_y_reenvio_idempotente(self):
        method = self.card()
        response = self.client.get(reverse("PlanesApp:contratar", args=["plus"]))
        token = response.context["form"].initial["token"]
        data = {"token": token, "method": method.pk, "amount": 1, "user": self.other.pk}
        first = self.client.post(reverse("PlanesApp:contratar", args=["plus"]), data)
        second = self.client.post(reverse("PlanesApp:contratar", args=["plus"]), data)
        self.assertEqual(first.url, second.url)
        self.assertEqual(SimulatedOperation.objects.count(), 1)
        sub = Subscription.objects.get(user=self.user)
        self.assertEqual(sub.amount_clp, 4990)
        self.assertEqual(self.user.profile.position_FK.permission_code, "RESTRICTED")

    def test_rechazo_no_cambia_plan_y_reintento_exitoso(self):
        rejected = self.card("4000000000000002")
        operation = self.buy(method=rejected)
        self.assertFalse(operation.approved)
        self.assertEqual(Subscription.objects.get(user=self.user).plan.code, "free")
        approved = self.buy(method=self.card())
        self.assertTrue(approved.approved)
        self.assertEqual(SimulatedOperation.objects.count(), 2)

    def test_fondos_insuficientes_historial_privado(self):
        op = self.buy(method=self.card("4000000000009995"))
        self.assertEqual(op.error_code, "insufficient")
        self.assertContains(
            self.client.get(reverse("PlanesApp:resultado", args=[op.reference])),
            "fondos insuficientes",
        )
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.get(
                reverse("PlanesApp:resultado", args=[op.reference])
            ).status_code,
            404,
        )
        self.assertNotContains(
            self.client.get(reverse("PlanesApp:historial")), self.user.email
        )

    def test_ids_ajenos_metodos_y_post_checkout(self):
        other = self.card(user=self.other)
        for route in ("metodo_eliminar", "metodo_predeterminado"):
            self.assertEqual(
                self.client.post(
                    reverse("PlanesApp:" + route, args=[other.pk]), {}
                ).status_code,
                404,
            )
        response = self.client.post(
            reverse("PlanesApp:contratar", args=["plus"]),
            {"token": proposal(self.user, self.plus, "purchase"), "method": other.pk},
        )
        self.assertTrue(response.context["form"].errors)
        self.assertFalse(SimulatedOperation.objects.exists())

    def test_token_otro_usuario_manipulado_vencido(self):
        method = self.card()
        for token in (proposal(self.other, self.plus, "purchase"), "invalid"):
            with self.assertRaises(ValidationError):
                execute(self.user, token, "purchase", self.plus, method.pk)
        with patch("django.core.signing.time.time", return_value=0):
            token = proposal(self.user, self.plus, "purchase")
        with self.assertRaises(ValidationError):
            execute(self.user, token, "purchase", self.plus, method.pk)

    def test_precio_version_cambiados_bloquean_confirmacion(self):
        method = self.card()
        token = proposal(self.user, self.plus, "purchase")
        self.plus.amount_clp = 5000
        self.plus.save()
        with self.assertRaises(ValidationError):
            execute(self.user, token, "purchase", self.plus, method.pk)
        self.assertFalse(SimulatedOperation.objects.exists())
        self.plus.amount_clp = 4990
        self.plus.save()
        stale = proposal(self.user, self.pro, "purchase")
        self.buy(method=method)
        with self.assertRaises(ValidationError):
            execute(self.user, stale, "purchase", self.pro, method.pk)

    def test_misma_clave_payload_distinto_rechazado(self):
        a = self.card()
        b = self.card("5555555555554444")
        token = proposal(self.user, self.plus, "purchase")
        execute(self.user, token, "purchase", self.plus, a.pk)
        with self.assertRaises(ValidationError):
            execute(self.user, token, "purchase", self.plus, b.pk)
        self.assertEqual(SimulatedOperation.objects.count(), 1)

    def test_fallo_db_despues_operacion_revierte_cambio(self):
        method = self.card()
        with patch.object(
            Subscription, "save", side_effect=IntegrityError("synthetic")
        ):
            with self.assertRaises(IntegrityError):
                self.buy(method=method)
        self.assertFalse(SimulatedOperation.objects.exists())
        self.assertFalse(Subscription.objects.exists())

    def test_plan_actual_no_cobra_cambio_pro_y_free_no_reembolso(self):
        method = self.card()
        self.buy(method=method)
        with self.assertRaises(ValidationError):
            self.buy(method=method)
        operation = self.buy(self.pro, method)
        self.assertEqual(operation.amount_clp, 9990)
        free = Plan.objects.get(code="free")
        operation = execute(
            self.user, proposal(self.user, free, "purchase"), "purchase", free
        )
        self.assertEqual(operation.amount_clp, 0)
        self.assertIsNone(Subscription.objects.get(user=self.user).end)

    def test_cancelacion_fin_y_revocacion_preservan_periodo(self):
        self.buy()
        sub = Subscription.objects.get(user=self.user)
        end = sub.end
        token = proposal(self.user, self.plus, "cancel")
        first = execute(self.user, token, "cancel")
        second = execute(self.user, token, "cancel")
        self.assertEqual(first.pk, second.pk)
        sub.refresh_from_db()
        self.assertEqual(sub.end, end)
        self.assertTrue(sub.cancel_at_period_end)
        execute(self.user, proposal(self.user, self.plus, "resume"), "resume")
        sub.refresh_from_db()
        self.assertFalse(sub.cancel_at_period_end)
        self.assertEqual(sub.end, end)

    def test_cancelacion_cumplida_free_sin_mutacion(self):
        self.buy()
        sub = Subscription.objects.get(user=self.user)
        execute(self.user, proposal(self.user, self.plus, "cancel"), "cancel")
        future = sub.end + timedelta(seconds=1)
        self.assertEqual(summary(self.user, future)["plan"].code, "free")
        with patch("PlanesApp.services.timezone.now", return_value=future):
            with self.assertRaises(ValidationError):
                execute(self.user, proposal(self.user, self.plus, "resume"), "resume")

    def test_revocar_cancelacion_requiere_tarjeta_vigente(self):
        method = self.card()
        self.buy(method=method)
        execute(self.user, proposal(self.user, self.plus, "cancel"), "cancel")
        method.year = 2020
        method.save(update_fields=["year"])
        before = SimulatedOperation.objects.count()
        with self.assertRaises(ValidationError):
            execute(self.user, proposal(self.user, self.plus, "resume"), "resume")
        self.assertEqual(SimulatedOperation.objects.count(), before)
        self.assertTrue(Subscription.objects.get(user=self.user).cancel_at_period_end)

    def test_seed_colision_no_modifica_cargo_ni_catalogo(self):
        position = Position.objects.get(user_position="Cliente público")
        position.permission_code = "ADMIN"
        position.save(update_fields=["permission_code"])
        before = list(Plan.objects.values_list("code", "amount_clp"))
        seed = import_module("PlanesApp.migrations.0002_catalogo_inicial").seed
        with self.assertRaises(RuntimeError):
            seed(apps, type("Schema", (), {"connection": connection})())
        position.refresh_from_db()
        self.assertEqual(position.permission_code, "ADMIN")
        self.assertEqual(list(Plan.objects.values_list("code", "amount_clp")), before)

    def test_catalogo_admin_preserva_free_y_precio_positivo(self):
        for code, amount, active in (
            ("free", 1, True),
            ("free", 0, False),
            ("plus", 0, True),
        ):
            plan = Plan.objects.get(code=code)
            form = PlanAdminForm(
                {
                    "code": code,
                    "name": plan.name,
                    "description": plan.description,
                    "amount_clp": amount,
                    "currency": "CLP",
                    "active": active,
                    "display_order": 0,
                },
                instance=plan,
            )
            self.assertFalse(form.is_valid())

    def test_renovacion_vencida_idempotencia_rechazo_sin_atrasos(self):
        good = self.card()
        self.buy(method=good)
        sub = Subscription.objects.get(user=self.user)
        sub.start = timezone.now() - timedelta(days=70)
        sub.end = timezone.now() - timedelta(days=40)
        sub.save()
        rejected = self.card("4000000000000002")
        old_end = sub.end
        bad = execute(
            self.user,
            proposal(self.user, self.plus, "renew"),
            "renew",
            self.plus,
            rejected.pk,
        )
        self.assertFalse(bad.approved)
        sub.refresh_from_db()
        self.assertEqual(sub.end, old_end)
        token = proposal(self.user, self.plus, "renew")
        a = execute(self.user, token, "renew", self.plus, good.pk)
        b = execute(self.user, token, "renew", self.plus, good.pk)
        self.assertEqual(a.pk, b.pk)
        self.assertGreater(a.period_start, old_end)
        self.assertEqual(a.amount_clp, 4990)

    def test_fecha_fin_mes_bisiesto_y_dst(self):
        zone = ZoneInfo("America/Santiago")
        for year, expected in ((2027, 28), (2028, 29)):
            target = month_after(datetime(year, 1, 31, 12, tzinfo=zone)).astimezone(
                zone
            )
            self.assertEqual((target.month, target.day), (2, expected))
        # September 2026 skips midnight on the 6th in Santiago.
        target = month_after(datetime(2026, 8, 6, 0, 30, tzinfo=zone)).astimezone(zone)
        self.assertEqual((target.day, target.hour, target.minute), (6, 1, 0))

    def test_eliminar_ultima_cancela_atomico_y_preserva_historial(self):
        method = self.card()
        op = self.buy(method=method)
        with self.assertRaises(ValidationError):
            remove_method(self.user, method)
        remove_method(self.user, method, proposal(self.user, self.plus, "cancel"))
        method.refresh_from_db()
        self.assertFalse(method.active)
        self.assertTrue(Subscription.objects.get(user=self.user).cancel_at_period_end)
        op.refresh_from_db()
        self.assertIn("4242", op.method_label)

    def test_restricciones_db_metodo_y_periodo(self):
        method = self.card()
        with self.assertRaises(IntegrityError), transaction.atomic():
            SimulatedPaymentMethod.objects.filter(pk=method.pk).update(month=13)
        self.buy(method=method)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Subscription.objects.filter(user=self.user).update(
                end=timezone.now() - timedelta(days=100)
            )

    def test_historial_paginado_no_ajeno(self):
        method = self.card("4000000000000002")
        for _ in range(11):
            self.buy(method=method)
        response = self.client.get(reverse("PlanesApp:historial"))
        self.assertEqual(response.context["paginator"].count, 11)
        self.assertEqual(len(response.context["operations"]), 10)

    def test_google_adapter_alta_y_email_verificado(self):
        from allauth.core import context

        request = RequestFactory().get("/accounts/google/login/callback/")
        request.user = AnonymousUser()
        request.session = self.client.session
        login = SocialLogin(
            user=User(username="google_demo", email="google@example.test"),
            account=SocialAccount(provider="google", uid="demo-unique"),
            email_addresses=[
                EmailAddress(email="google@example.test", verified=True, primary=True)
            ],
        )
        with context.request_context(request):
            user = PublicSocialAccountAdapter().save_user(request, login)
        self.assertEqual(user.profile.position_FK.permission_code, "RESTRICTED")
        self.assertFalse(user.has_usable_password())
        self.assertTrue(EmailAddress.objects.get(user=user).verified)
        self.assertEqual(Subscription.objects.get(user=user).plan.code, "free")

    def test_google_rollback_y_sin_fusion_automatica(self):
        self.assertFalse(
            __import__(
                "django.conf", fromlist=["settings"]
            ).settings.SOCIALACCOUNT_EMAIL_AUTHENTICATION
        )
        from allauth.core import context

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        request.session = self.client.session
        login = SocialLogin(
            user=User(username="google_fail", email="google-fail@example.test"),
            account=SocialAccount(provider="google", uid="fail-demo"),
            email_addresses=[],
        )
        with context.request_context(request), patch(
            "UsuarioApp.adapters.provision_public_user",
            side_effect=IntegrityError("synthetic"),
        ):
            with self.assertRaises(IntegrityError):
                PublicSocialAccountAdapter().save_user(request, login)
        self.assertFalse(User.objects.filter(username="google_fail").exists())
        self.assertFalse(SocialAccount.objects.filter(uid="fail-demo").exists())

    def test_google_sin_configuracion_interfaz_y_contratos(self):
        self.assertContains(
            self.client.get(reverse("socialaccount_connections")),
            "aún no está configurada",
        )
        self.client.logout()
        self.assertNotContains(
            self.client.get(reverse("account_login")), "Continuar con Google"
        )
        with override_settings(GOOGLE_OAUTH_ENABLED=True):
            self.assertContains(
                self.client.get(reverse("account_signup")), "Continuar con Google"
            )

    def google_state(self):
        response = self.client.post(reverse("google_login"))
        self.assertEqual(response.status_code, 302)
        query = parse_qs(urlparse(response.url).query)
        self.assertIn("code_challenge", query)
        return query["state"][0]

    def mocked_google_login(self, login):
        def complete(adapter, request, app, token, **kwargs):
            login.provider = adapter.get_provider()
            return login

        return patch(
            "allauth.socialaccount.providers.google.views.GoogleOAuth2Adapter.complete_login",
            autospec=True,
            side_effect=complete,
        )

    @override_settings(SOCIALACCOUNT_PROVIDERS=GOOGLE_TEST, GOOGLE_OAUTH_ENABLED=True)
    def test_google_callback_mock_alta_y_login_repetido_preservan_cargo(self):
        self.client.logout()

        def social():
            return SocialLogin(
                user=User(username="oauth_demo", email="oauth@example.test"),
                account=SocialAccount(provider="google", uid="callback-demo"),
                email_addresses=[
                    EmailAddress(
                        email="oauth@example.test", verified=True, primary=True
                    )
                ],
            )

        for _ in range(2):
            state = self.google_state()
            with patch(
                "allauth.socialaccount.providers.google.views.GoogleOAuth2Adapter.get_access_token_data",
                return_value={"access_token": "demo-token"},
            ), self.mocked_google_login(social()):
                response = self.client.get(
                    reverse("google_callback"), {"state": state, "code": "demo-code"}
                )
            self.assertEqual(response.status_code, 302)
            user = User.objects.get(email="oauth@example.test")
            self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
            self.assertEqual(Subscription.objects.filter(user=user).count(), 1)
            position, _ = Position.objects.get_or_create(
                user_position="Operador demo", defaults={"permission_code": "MANAGER"}
            )
            user.profile.position_FK = position
            user.profile.save()
            self.client.logout()
        user.refresh_from_db()
        self.assertEqual(user.profile.position_FK.permission_code, "MANAGER")
        self.assertEqual(SocialAccount.objects.filter(uid="callback-demo").count(), 1)
        from allauth.socialaccount.models import SocialToken

        self.assertFalse(SocialToken.objects.exists())

    @override_settings(SOCIALACCOUNT_PROVIDERS=GOOGLE_TEST, GOOGLE_OAUTH_ENABLED=True)
    def test_google_callback_colision_no_fusiona_ni_autentica(self):
        self.client.logout()
        before = User.objects.count()
        login = SocialLogin(
            user=User(username="colision_demo", email=self.user.email),
            account=SocialAccount(provider="google", uid="collision-demo"),
            email_addresses=[
                EmailAddress(email=self.user.email, verified=True, primary=True)
            ],
        )
        state = self.google_state()
        with patch(
            "allauth.socialaccount.providers.google.views.GoogleOAuth2Adapter.get_access_token_data",
            return_value={"access_token": "demo-token"},
        ), self.mocked_google_login(login):
            response = self.client.get(
                reverse("google_callback"), {"state": state, "code": "demo-code"}
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.count(), before)
        self.assertFalse(SocialAccount.objects.filter(uid="collision-demo").exists())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.position_FK.permission_code, "RESTRICTED")

    @override_settings(SOCIALACCOUNT_PROVIDERS=GOOGLE_TEST, GOOGLE_OAUTH_ENABLED=True)
    def test_google_callback_cancelacion_estado_invalido_y_error(self):
        self.client.logout()
        before = User.objects.count()
        state = self.google_state()
        response = self.client.get(
            reverse("google_callback"), {"state": state, "error": "access_denied"}
        )
        self.assertRedirects(response, reverse("socialaccount_login_cancelled"))
        response = self.client.get(
            reverse("google_callback"), {"state": "invalid", "code": "demo-code"}
        )
        self.assertEqual(response.status_code, 401)
        state = self.google_state()
        response = self.client.get(
            reverse("google_callback"), {"state": state, "error": "server_error"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(User.objects.count(), before)
        self.assertFalse(SocialAccount.objects.exists())
