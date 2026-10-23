import json
import re
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.test import Client, RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from PlanesApp.dashboard import subscription_dashboard
from PlanesApp.models import Plan, SimulatedOperation, Subscription
from PlanesApp.services import summary
from UsuarioApp.models import Position, Profile, UserVisualPreference

from .views import HomeView


class DashboardTests(TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 6, 12, tzinfo=ZoneInfo("America/Santiago"))
        self.plans = {p.code: p for p in Plan.objects.all()}
        self.root = User.objects.create_user("dashboard_root", is_superuser=True)

    def subscribe(self, name, code="free", active=True, **kwargs):
        user = User.objects.create_user(name, is_active=active)
        plan = self.plans[code]
        defaults = {
            "plan": plan,
            "plan_name": plan.name,
            "amount_clp": plan.amount_clp,
        }
        if plan.amount_clp:
            defaults.update(
                start=self.now - timedelta(days=30), end=self.now + timedelta(days=3)
            )
        Subscription.objects.create(user=user, **{**defaults, **kwargs})
        return user

    def operation(self, user, kind="purchase", amount=4990, approved=True, date=None):
        plan = self.plans["plus"]
        op = SimulatedOperation.objects.create(
            user=user,
            plan=plan,
            plan_name="Precio anterior de prueba",
            amount_clp=amount,
            kind=kind,
            approved=approved,
            idempotency_key=uuid.uuid4(),
            payload="demo",
        )
        SimulatedOperation.objects.filter(pk=op.pk).update(created_at=date or self.now)

    def test_estados_poblacion_y_distribucion_coinciden_con_resumen_propio(self):
        users = [
            self.subscribe("free"),
            self.subscribe("plus", "plus"),
            self.subscribe("pro", "pro", end=self.now),
            self.subscribe("hogar", "hogar", cancel_at_period_end=True),
            self.subscribe("cancelada", "pro", end=self.now, cancel_at_period_end=True),
        ]
        self.subscribe("inactiva", "plus", active=False)
        User.objects.create_user("sin_fila")
        snapshot = list(Subscription.objects.values())
        data = subscription_dashboard(self.now)
        self.assertEqual(
            (
                data["registered"],
                data["paid_current"],
                data["expired"],
                data["cancellation_pending"],
            ),
            (5, 2, 1, 1),
        )
        quantities = {item["code"]: item["total"] for item in data["distribution"]}
        self.assertEqual(quantities, {"free": 2, "plus": 1, "pro": 1, "hogar": 1})
        expected = {code: 0 for code in self.plans}
        for user in users:
            expected[summary(user, self.now)["plan"].code] += 1
        self.assertEqual(quantities, expected)
        self.assertEqual(sum(quantities.values()), data["registered"])
        self.assertEqual(snapshot, list(Subscription.objects.values()))

    def test_limite_cancelacion_es_lectura_y_no_vencimiento_persistido(self):
        self.subscribe("limite", "plus", end=self.now, cancel_at_period_end=True)
        before = subscription_dashboard(self.now - timedelta(microseconds=1))
        after = subscription_dashboard(self.now)
        self.assertEqual(
            (before["paid_current"], before["cancellation_pending"]), (1, 1)
        )
        self.assertEqual(
            (after["paid_current"], after["expired"], after["cancellation_pending"]),
            (0, 0, 0),
        )
        self.assertEqual(after["distribution"][0]["total"], 1)
        self.assertEqual(Subscription.objects.get().plan.code, "plus")

    def test_plan_historico_inactivo_no_pierde_suscripciones(self):
        self.subscribe("historica", "pro", end=self.now)
        Plan.objects.filter(code="pro").update(active=False)
        data = subscription_dashboard(self.now)
        historical = next(row for row in data["distribution"] if row["code"] == "pro")
        self.assertEqual(historical["total"], 1)
        self.assertFalse(historical["active"])

    def test_sin_filas_y_catalogo_vacio_no_crean_datos(self):
        data = subscription_dashboard(self.now)
        self.assertEqual(data["registered"], 0)
        self.assertTrue(all(row["share"] == 0 for row in data["distribution"]))
        Plan.objects.all().delete()
        self.client.force_login(self.root)
        response = self.client.get(reverse("Home"))
        self.assertContains(response, "El catálogo aún no tiene planes registrados")
        self.assertContains(response, "Aún no hay suscripciones")
        self.assertEqual(response.context["dashboard"]["distribution"], [])
        self.assertFalse(Subscription.objects.exists())
        self.assertFalse(UserVisualPreference.objects.exists())

    def test_volumen_solo_operaciones_monetarias_aprobadas_del_mes_local(self):
        month_start = self.now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Octubre 00:00 en Santiago no equivale a octubre 00:00 UTC.
        self.operation(self.root, amount=100, date=month_start)
        self.operation(self.root, kind="change", amount=200)
        self.operation(self.root, kind="renew", amount=300)
        self.operation(
            self.root, amount=900, date=month_start - timedelta(microseconds=1)
        )
        self.operation(self.root, amount=900, date=self.now + timedelta(microseconds=1))
        self.operation(self.root, amount=900, approved=False)
        for kind in ("free", "cancel", "resume"):
            self.operation(self.root, kind=kind, amount=900)
        inactive = User.objects.create_user("operacion_historica", is_active=False)
        self.operation(inactive, amount=400)
        Plan.objects.filter(code="plus").update(amount_clp=99999)
        data = subscription_dashboard(self.now)
        self.assertEqual((data["volume_clp"], data["monetary_count"]), (1000, 4))
        self.assertEqual(data["volume_label"], "$1.000")
        self.assertEqual(data["month_start"], month_start)

    def test_consultas_acotadas_independientes_del_numero_de_cuentas(self):
        with self.assertNumQueries(4):
            subscription_dashboard(self.now)
        for index in range(20):
            self.subscribe(f"masiva_{index}", "plus")
        with self.assertNumQueries(4):
            data = subscription_dashboard(self.now)
        self.assertEqual(data["registered"], 20)

    def test_matriz_de_lectura_y_menu_coherentes_sin_consultas_globales_para_clientes(
        self,
    ):
        cases = [
            ("ADMIN", False, False, True),
            ("MANAGER", False, False, True),
            ("RESTRICTED", False, False, False),
            (None, False, False, False),
            (None, False, True, False),
            (None, True, False, True),
            ("RESTRICTED", True, False, True),
        ]
        for index, (code, root, staff, allowed) in enumerate(cases):
            with self.subTest(code=code, root=root, staff=staff):
                user = User.objects.create_user(
                    f"actor_{index}", is_superuser=root, is_staff=staff
                )
                if code:
                    position = Position.objects.create(
                        user_position=f"Cargo actor {index}", permission_code=code
                    )
                    Profile.objects.create(user_FK=user, position_FK=position)
                self.client.force_login(user)
                with patch(
                    "homeApp.views.subscription_dashboard", wraps=subscription_dashboard
                ) as service:
                    with CaptureQueriesContext(connection) as queries:
                        response = self.client.get(reverse("Home"))
                    self.assertEqual(service.call_count, int(allowed))
                if allowed:
                    self.assertContains(response, "Resumen de suscripciones")
                else:
                    self.assertRedirects(
                        response,
                        reverse("CuidadosApp:panel"),
                        fetch_redirect_response=False,
                    )
                    self.assertFalse(
                        any(
                            'FROM "auth_user"' in q["sql"] and "ORDER BY" in q["sql"]
                            for q in queries
                        )
                    )
                page = self.client.get(reverse("PlanesApp:mi_suscripcion"))
                self.assertEqual(page.status_code, 200)
                has_home_link = bool(
                    re.search(r'href="/" class="nav-link"', page.content.decode())
                )
                self.assertEqual(has_home_link, allowed)

    def test_anonimo_inactivo_y_perfil_sin_cargo_sin_acceso_global(self):
        factory = RequestFactory()
        inactive = User.objects.create_user(
            "inactive_root", is_active=False, is_superuser=True
        )
        no_position = User.objects.create_user("perfil_sin_cargo")
        Profile.objects.create(user_FK=no_position)
        for user in (AnonymousUser(), inactive, no_position):
            request = factory.get(reverse("Home"))
            request.user = user
            with patch("homeApp.views.subscription_dashboard") as service:
                if user == inactive:
                    with self.assertRaises(PermissionDenied):
                        HomeView.as_view()(request)
                else:
                    response = HomeView.as_view()(request)
                    self.assertEqual(response.status_code, 302)
                    destination = (
                        reverse("account_login")
                        if not user.is_authenticated
                        else reverse("CuidadosApp:panel")
                    )
                    self.assertTrue(response.url.startswith(destination))
                service.assert_not_called()

    def test_selector_compartido_svg_modo_y_post_propio_conservados(self):
        user = self.subscribe("selector_cliente")
        for actor in (self.root, user):
            self.client.force_login(actor)
            route = "Home" if actor.is_superuser else "PlanesApp:mi_suscripcion"
            for mode, action in (("light", "oscuro"), ("dark", "claro")):
                response = self.client.get(reverse(route))
                self.assertContains(response, f'aria-label="Activar modo {action}"')
                form = re.search(
                    r'<form[^>]*class="visual-mode-form".*?</form>',
                    response.content.decode(),
                    re.DOTALL,
                ).group()
                self.assertIn('<svg aria-hidden="true" focusable="false"', form)
                self.assertIn("csrfmiddlewaretoken", form)
                self.assertNotIn("☀", form)
                if mode == "light":
                    post = self.client.post(reverse("VisualMode"), {"mode": "dark"})
                    self.assertRedirects(
                        post, reverse("Home"), fetch_redirect_response=False
                    )
                    self.assertEqual(
                        UserVisualPreference.objects.get(user=actor).mode, "dark"
                    )
        self.assertEqual(UserVisualPreference.objects.get(user=self.root).mode, "dark")
        self.assertEqual(UserVisualPreference.objects.get(user=user).mode, "dark")
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(user)
        self.assertEqual(
            csrf_client.post(reverse("VisualMode"), {"mode": "light"}).status_code, 403
        )
        self.assertEqual(
            self.client.post(reverse("VisualMode"), {"mode": "invalid"}).status_code,
            400,
        )
        self.assertEqual(UserVisualPreference.objects.get(user=user).mode, "dark")

    def test_nombres_de_planes_se_serializan_sin_inyeccion_de_script(self):
        self.subscribe("escaped", "plus")
        name = '</script><script>alert("demo")</script>'
        Plan.objects.filter(code="plus").update(name=name)
        self.client.force_login(self.root)
        response = self.client.get(reverse("Home"))
        html = response.content.decode()
        self.assertNotIn(name, html)
        serialized = re.search(
            r'<script id="dashboard-plan-data" type="application/json">(.*?)</script>',
            html,
            re.DOTALL,
        ).group(1)
        self.assertIn(name, [row["name"] for row in json.loads(serialized)])
        self.assertIn("\\u003C", serialized)
