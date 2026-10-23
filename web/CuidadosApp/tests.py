from concurrent.futures import ThreadPoolExecutor
from datetime import date, time, timedelta
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch
from zoneinfo import ZoneInfo

from allauth.account.models import EmailAddress
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import (
    DatabaseError,
    IntegrityError,
    close_old_connections,
    connection,
    transaction,
)
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from PlanesApp.forms import PaymentMethodForm
from PlanesApp.models import Plan, SimulatedOperation, Subscription
from PlanesApp.services import add_method, execute, proposal, remove_method
from UsuarioApp.models import Position, Profile

from .capacity import capacity_state, choose_capacity, fingerprint
from .forms import MedicationForm, PatientForm, TaskForm
from .models import (
    CapacitySelection,
    CareEvent,
    CareGuide,
    CareTask,
    Medication,
    MedicationTime,
    Patient,
    PostureTimer,
    ReminderReceipt,
)
from .scheduling import agenda, claim_reminder, reminders, wall_instant
from .services import (
    action_token,
    configure_timer,
    correct_event,
    record_daily,
    record_posture,
    save_daily,
    save_patient,
    set_patient_active,
)


class CareTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("cuidador_demo", email="demo@example.test")
        self.other = User.objects.create_user("otra_demo", email="otra@example.test")
        self.now = timezone.now()
        self.patient = Patient.objects.create(owner=self.user, name="Ana Demo")
        self.foreign = Patient.objects.create(
            owner=self.other, name="Paciente privado de otra cuenta"
        )
        self.client.force_login(self.user)
        self.guide = CareGuide.objects.get(code="supina")

    def paid(self, code="plus"):
        plan = Plan.objects.get(code=code)
        return Subscription.objects.update_or_create(
            user=self.user,
            defaults={
                "plan": plan,
                "plan_name": plan.name,
                "amount_clp": plan.amount_clp,
                "start": self.now - timedelta(days=1),
                "end": self.now + timedelta(days=29),
                "cancel_at_period_end": False,
            },
        )[0]

    def card(self, declined=False):
        EmailAddress.objects.get_or_create(
            user=self.user, email=self.user.email, defaults={"verified": True}
        )
        form = PaymentMethodForm(
            {
                "holder": "Ana Demo",
                "number": "4000000000000002" if declined else "4242424242424242",
                "expiry": "12/30",
                "cvc": "123",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        return add_method(self.user, form.cleaned_data)

    def posture(self, interval=120):
        timer = PostureTimer.objects.filter(patient=self.patient).first()
        token = action_token(
            self.user, self.patient, "posture", version=timer.generation if timer else 0
        )
        return record_posture(self.user, self.patient.pk, token, self.guide, interval)

    def medication(self):
        med = Medication.objects.create(
            patient=self.patient,
            name="Medicamento de prueba",
            dose="Dosis ficticia indicada",
            version=1,
            schedule_effective_at=wall_instant(
                timezone.localdate(self.now), time(0, 0)
            ),
        )
        MedicationTime.objects.create(medication=med, time=time(0, 0))
        return med

    def test_ownership_all_roles_root_and_no_profile(self):
        foreign_med = Medication.objects.create(
            patient=self.foreign, name="Privado", dose="Prueba"
        )
        for code, root in [
            ("ADMIN", False),
            ("MANAGER", False),
            ("RESTRICTED", False),
            (None, True),
            (None, False),
        ]:
            with self.subTest(code=code, root=root):
                Profile.objects.filter(user_FK=self.user).delete()
                if code:
                    pos = Position.objects.create(
                        user_position=f"Care {code}", permission_code=code
                    )
                    Profile.objects.create(user_FK=self.user, position_FK=pos)
                self.user.is_superuser = root
                self.user.save()
                for route in ("panel", "patients", "agenda", "guides", "reminders"):
                    response = self.client.get(reverse(f"CuidadosApp:{route}"))
                    self.assertEqual(response.status_code, 200)
                    self.assertNotContains(response, self.foreign.name)
                for route in ("patient", "patient_edit", "posture", "history", "timer"):
                    url = reverse(f"CuidadosApp:{route}", args=[self.foreign.pk])
                    self.assertEqual(self.client.get(url).status_code, 404)
                    self.assertEqual(self.client.post(url, {}).status_code, 404)
                url = reverse(
                    "CuidadosApp:medication_edit",
                    args=[self.patient.pk, foreign_med.pk],
                )
                self.assertEqual(self.client.get(url).status_code, 404)
                self.assertEqual(self.client.post(url, {}).status_code, 404)

    def test_anon_inactive_csrf_and_private_cache(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("CuidadosApp:panel")).status_code, 302)
        self.user.is_active = False
        self.user.save()
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("CuidadosApp:panel")).status_code, 302)
        self.user.is_active = True
        self.user.save()
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(
            client.post(
                reverse("CuidadosApp:patient_new"), {"name": "Otra Demo"}
            ).status_code,
            403,
        )
        self.assertIn(
            "no-store",
            client.get(reverse("CuidadosApp:patient", args=[self.patient.pk]))[
                "Cache-Control"
            ],
        )

    def test_patient_limits_and_owner_payload_ignored(self):
        response = self.client.post(
            reverse("CuidadosApp:patient_new"),
            {"name": "Otra Demo", "owner": self.other.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Patient.objects.filter(owner=self.user).count(), 1)
        self.paid()
        for name in ("Berta Demo", "Carlos Demo"):
            response = self.client.post(
                reverse("CuidadosApp:patient_new"),
                {"name": name, "owner": self.other.pk},
            )
            self.assertEqual(response.status_code, 302)
        self.assertEqual(Patient.objects.filter(owner=self.user).count(), 3)
        with self.assertRaises(ValidationError):
            save_patient(self.user, {"name": "Excede Demo"})
        self.paid("pro")
        for index in range(6):
            save_patient(self.user, {"name": f"Ilimitado {index}"})
        self.assertEqual(capacity_state(self.user)["count"], 9)

    def test_patient_validation_stale_edit_and_immutable_owner(self):
        self.assertFalse(
            PatientForm({"name": "Ana", "birth_date": "2099-01-01"}).is_valid()
        )
        self.assertFalse(
            PatientForm({"name": "Ana", "contact_name": "Incompleto"}).is_valid()
        )
        self.assertFalse(
            PatientForm(
                {
                    "name": "Ana",
                    "contact_name": "Demo",
                    "contact_phone": "abcde",
                    "contact_relation": "Demo",
                }
            ).is_valid()
        )
        response = self.client.post(
            reverse("CuidadosApp:patient_edit", args=[self.patient.pk]),
            {"name": "Ana Editada", "version": 0, "owner": self.other.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.owner, self.user)
        with self.assertRaises(ValidationError):
            save_patient(self.user, {"name": "Viejo"}, self.patient.pk, 0)

    def test_archive_pauses_and_reactivation_preserves_history(self):
        self.posture()
        token = action_token(self.user, self.patient, "archive", version=0)
        set_patient_active(self.user, self.patient.pk, token, False)
        self.patient.refresh_from_db()
        self.assertTrue(PostureTimer.objects.get(patient=self.patient).paused)
        self.assertEqual(reminders(self.user), [])
        with self.assertRaises(ValidationError):
            self.posture()
        other = save_patient(self.user, {"name": "Reemplazo Demo"})
        token = action_token(
            self.user, self.patient, "reactivate", version=self.patient.version
        )
        with self.assertRaises(ValidationError):
            set_patient_active(self.user, self.patient.pk, token, True)
        set_patient_active(
            self.user,
            other.pk,
            action_token(self.user, other, "archive", version=other.version),
            False,
        )
        set_patient_active(self.user, self.patient.pk, token, True)
        self.assertEqual(CareEvent.objects.count(), 1)
        self.assertTrue(PostureTimer.objects.get(patient=self.patient).paused)

    def test_reactivation_only_resumes_upcoming_daily_slots(self):
        med = self.medication()
        self.assertTrue(agenda(self.user)[0]["overdue"])
        old_token = agenda(self.user)[0]["token"]
        set_patient_active(
            self.user,
            self.patient.pk,
            action_token(self.user, self.patient, "archive", version=0),
            False,
        )
        self.patient.refresh_from_db()
        set_patient_active(
            self.user,
            self.patient.pk,
            action_token(
                self.user, self.patient, "reactivate", version=self.patient.version
            ),
            True,
        )
        self.assertEqual(agenda(self.user), [])
        self.assertEqual(reminders(self.user), [])
        med.refresh_from_db()
        self.assertEqual(med.version, 2)
        with self.assertRaises(ValidationError):
            record_daily(self.user, self.patient.pk, old_token, "done", "")

    def test_sensitive_admin_and_generic_account_delete(self):
        for model in (Patient, Medication, CareEvent, PostureTimer, CapacitySelection):
            self.assertNotIn(model, admin.site._registry)
        with self.assertRaises(ProtectedError) as caught:
            self.user.delete()
        self.assertNotIn(self.patient.name, str(caught.exception))

    def test_posture_intervals_replay_and_server_clock(self):
        for interval in (60, 90, 120):
            with patch("CuidadosApp.services.timezone.now", return_value=self.now):
                event = self.posture(interval)
            timer = PostureTimer.objects.get(patient=self.patient)
            self.assertEqual(timer.next_due_at, self.now + timedelta(minutes=interval))
            self.assertEqual(event.occurred_at, self.now)
        token = action_token(self.user, self.patient, "posture", version=3)
        first = record_posture(self.user, self.patient.pk, token, self.guide, 90)
        self.assertEqual(
            record_posture(self.user, self.patient.pk, token, self.guide, 90).pk,
            first.pk,
        )
        with self.assertRaises(ValidationError):
            record_posture(self.user, self.patient.pk, token, self.guide, 60)
        timer_before = PostureTimer.objects.get(patient=self.patient).next_due_at
        self.client.get(reverse("CuidadosApp:patient", args=[self.patient.pk]))
        self.client.get(reverse("CuidadosApp:panel"))
        self.assertEqual(
            PostureTimer.objects.get(patient=self.patient).next_due_at, timer_before
        )

    def test_timer_change_pause_resume_and_stale_generation(self):
        event = self.posture()

        def token():
            return action_token(
                self.user,
                self.patient,
                "timer",
                version=PostureTimer.objects.get(patient=self.patient).generation,
            )

        old = token()
        configure_timer(self.user, self.patient.pk, old, "interval", 60)
        self.assertEqual(
            PostureTimer.objects.get(patient=self.patient).next_due_at,
            event.occurred_at + timedelta(minutes=60),
        )
        with self.assertRaises(ValidationError):
            configure_timer(self.user, self.patient.pk, old, "pause", 60)
        configure_timer(self.user, self.patient.pk, token(), "pause", 60)
        self.assertIsNone(PostureTimer.objects.get(patient=self.patient).next_due_at)
        with patch(
            "CuidadosApp.services.timezone.now",
            return_value=self.now + timedelta(hours=4),
        ):
            configure_timer(self.user, self.patient.pk, token(), "resume", 90)
        self.assertEqual(
            PostureTimer.objects.get(patient=self.patient).next_due_at,
            self.now + timedelta(hours=4, minutes=90),
        )
        self.assertEqual(CareEvent.objects.count(), 1)

    def test_reminder_ten_minutes_due_claim_and_new_generation(self):
        self.posture()
        timer = PostureTimer.objects.get(patient=self.patient)
        self.assertEqual(
            reminders(self.user, timer.next_due_at - timedelta(minutes=10, seconds=1)),
            [],
        )
        soon = reminders(self.user, timer.next_due_at - timedelta(minutes=10))[0]
        self.assertTrue(soon["key"].endswith("soon"))
        with patch(
            "CuidadosApp.scheduling.timezone.now",
            return_value=timer.next_due_at - timedelta(minutes=5),
        ):
            self.assertTrue(claim_reminder(self.user, soon["token"]))
            self.assertFalse(claim_reminder(self.user, soon["token"]))
        self.assertEqual(CareEvent.objects.count(), 1)
        due = reminders(self.user, timer.next_due_at)[0]
        self.assertTrue(due["key"].endswith("due"))
        self.posture()
        with self.assertRaises(ValidationError):
            claim_reminder(self.user, due["token"])

    def test_foreign_reminder_claim_and_signed_actions_rejected(self):
        self.posture()
        timer = PostureTimer.objects.get(patient=self.patient)
        token = reminders(self.user, timer.next_due_at)[0]["token"]
        with self.assertRaises(ValidationError):
            claim_reminder(self.other, token)
        token = action_token(self.other, self.foreign, "posture")
        with self.assertRaises(ValidationError):
            record_posture(self.user, self.patient.pk, token, self.guide, 60)
        self.assertEqual(ReminderReceipt.objects.count(), 0)

    def test_medications_multiple_hours_errors_and_versions(self):
        for hours in ("25:00", "08:00,08:00", "8:00", ""):
            self.assertFalse(
                MedicationForm(
                    {"name": "Demo", "dose": "Prueba", "hours": hours}
                ).is_valid()
            )
        form = MedicationForm(
            {
                "name": "Demo",
                "dose": "Texto indicado",
                "hours": "08:00, 20:00",
                "active": True,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        med = save_daily(self.user, self.patient.pk, form)
        self.assertEqual(med.times.count(), 2)
        form = MedicationForm(
            {
                "name": "Demo",
                "dose": "Nuevo",
                "hours": "09:00",
                "active": True,
                "version": 0,
            },
            instance=med,
        )
        self.assertTrue(form.is_valid(), form.errors)
        with self.assertRaises(ValidationError):
            save_daily(self.user, self.patient.pk, form, med.pk)

    def test_daily_event_snapshots_omission_and_duplicates(self):
        med = self.medication()
        item = agenda(self.user)[0]
        with self.assertRaises(ValidationError):
            record_daily(self.user, self.patient.pk, item["token"], "omitted", "")
        event = record_daily(
            self.user, self.patient.pk, item["token"], "done", "Confirmación ficticia"
        )
        self.assertEqual(
            record_daily(
                self.user,
                self.patient.pk,
                item["token"],
                "done",
                "Confirmación ficticia",
            ).pk,
            event.pk,
        )
        with self.assertRaises(ValidationError):
            record_daily(
                self.user,
                self.patient.pk,
                agenda(self.user)[0]["token"],
                "done",
                "Nuevo intento",
            )
        med.dose = "Cambio futuro"
        med.version += 1
        med.save()
        event.refresh_from_db()
        self.assertEqual(event.snapshot["dose"], "Dosis ficticia indicada")
        self.assertEqual(event.patient.owner, self.user)

    def test_edited_schedule_rejects_old_occurrence(self):
        med = self.medication()
        token = agenda(self.user)[0]["token"]
        med.version += 1
        med.save()
        with self.assertRaises(ValidationError):
            record_daily(self.user, self.patient.pk, token, "done", "")

    def test_editing_dose_does_not_reopen_completed_daily_slot(self):
        med = self.medication()
        event = record_daily(
            self.user, self.patient.pk, agenda(self.user)[0]["token"], "done", "Prueba"
        )
        med.dose = "Dosis ficticia corregida"
        med.version += 1
        med.schedule_effective_at = timezone.now()
        med.save()
        item = agenda(self.user)[0]
        self.assertEqual(item["event"].pk, event.pk)
        self.assertEqual(item["dose"], "Dosis ficticia indicada")
        with self.assertRaises(ValidationError):
            record_daily(
                self.user,
                self.patient.pk,
                item["token"],
                "done",
                "Segunda toma ficticia",
            )

    def test_new_past_schedule_does_not_invent_overdue_activity(self):
        med = self.medication()
        med.schedule_effective_at = self.now
        med.save()
        self.assertEqual(agenda(self.user), [])
        tomorrow = self.now + timedelta(days=1)
        self.assertEqual(len(agenda(self.user, tomorrow)), 1)

    def test_invalid_patient_filter_returns_not_found(self):
        response = self.client.get(
            reverse("CuidadosApp:agenda"), {"patient": "invalido"}
        )
        self.assertEqual(response.status_code, 404)

    def test_tasks_manual_daily_ranges_and_omission(self):
        task = CareTask.objects.create(
            patient=self.patient, name="Actividad de prueba", notes="Ficticia"
        )
        items = agenda(self.user)
        self.assertEqual(len(items), 1)
        self.assertIsNone(items[0]["due"])
        self.assertEqual(reminders(self.user), [])
        record_daily(
            self.user, self.patient.pk, items[0]["token"], "omitted", "Omisión ficticia"
        )
        self.assertEqual(agenda(self.user)[0]["event"].status, "omitted")
        task.end_date = timezone.localdate() - timedelta(days=1)
        task.save()
        self.assertEqual(agenda(self.user), [])
        self.assertFalse(
            TaskForm(
                {"name": "Demo", "start_date": "2026-10-08", "end_date": "2026-10-07"}
            ).is_valid()
        )

    def test_correction_preserves_original_and_timer(self):
        original = self.posture()
        due = PostureTimer.objects.get(patient=self.patient).next_due_at
        token = action_token(self.user, self.patient, "correction", subject=original.pk)
        correction = correct_event(
            self.user, self.patient.pk, original.pk, token, "Nota corregida de prueba"
        )
        self.assertEqual(correction.corrected_event, original)
        original.refresh_from_db()
        self.assertEqual(original.note, "")
        self.assertEqual(
            PostureTimer.objects.get(patient=self.patient).next_due_at, due
        )
        self.assertEqual(
            correct_event(
                self.user,
                self.patient.pk,
                original.pk,
                token,
                "Nota corregida de prueba",
            ).pk,
            correction.pk,
        )

    def test_dst_gap_fold_and_midnight_not_duplicate(self):
        gap = wall_instant(date(2026, 9, 6), time(0, 30))
        self.assertEqual(
            gap.astimezone(ZoneInfo("America/Santiago")).strftime("%H:%M"), "01:00"
        )
        repeated = wall_instant(date(2026, 4, 4), time(23, 30))
        self.assertEqual(repeated.astimezone(ZoneInfo("America/Santiago")).fold, 0)
        self.medication()
        before = self.now.astimezone(ZoneInfo("America/Santiago")).replace(
            hour=23, minute=59
        )
        after = before + timedelta(minutes=2)
        self.assertEqual(
            len({i["key"] for i in agenda(self.user, after)}),
            len(agenda(self.user, after)),
        )
        self.assertNotEqual(
            agenda(self.user, before)[0]["key"],
            next(i for i in agenda(self.user, after) if i["date"] == after.date())[
                "key"
            ],
        )

    def test_get_does_not_create_care_or_business_rows(self):
        before = (
            Patient.objects.count(),
            CareEvent.objects.count(),
            ReminderReceipt.objects.count(),
            PostureTimer.objects.count(),
            Subscription.objects.count(),
        )
        for route, args in [
            ("panel", []),
            ("patients", []),
            ("patient", [self.patient.pk]),
            ("guides", []),
            ("agenda", []),
            ("reminders", []),
            ("posture", [self.patient.pk]),
            ("history", [self.patient.pk]),
        ]:
            response = self.client.get(reverse(f"CuidadosApp:{route}", args=args))
            self.assertEqual(response.status_code, 200)
        self.assertEqual(
            before,
            (
                Patient.objects.count(),
                CareEvent.objects.count(),
                ReminderReceipt.objects.count(),
                PostureTimer.objects.count(),
                Subscription.objects.count(),
            ),
        )

    def test_plan_reduction_requires_choice_and_payment_failure_preserves_patients(
        self,
    ):
        self.paid("pro")
        extra = [
            Patient.objects.create(owner=self.user, name=f"Demo {i}") for i in range(3)
        ]
        plan = Plan.objects.get(code="plus")
        card = self.card(declined=True)
        token = proposal(self.user, plan, "purchase")
        with self.assertRaises(ValidationError):
            execute(self.user, token, "purchase", plan, card.pk)
        operation = execute(
            self.user,
            token,
            "purchase",
            plan,
            card.pk,
            [self.patient.pk, extra[0].pk, extra[1].pk],
        )
        self.assertFalse(operation.approved)
        self.assertEqual(
            Patient.objects.filter(owner=self.user, active=True).count(), 4
        )
        card = self.card()
        token = proposal(self.user, plan, "purchase")
        operation = execute(
            self.user,
            token,
            "purchase",
            plan,
            card.pk,
            [self.patient.pk, extra[0].pk, extra[1].pk],
        )
        self.assertTrue(operation.approved)
        self.assertEqual(
            Patient.objects.filter(owner=self.user, active=True).count(), 3
        )
        self.assertEqual(
            execute(
                self.user,
                token,
                "purchase",
                plan,
                card.pk,
                [self.patient.pk, extra[0].pk, extra[1].pk],
            ).pk,
            operation.pk,
        )
        self.assertFalse(Patient.objects.get(pk=extra[2].pk).active)

    def test_cancel_selection_effective_at_end_readonly_and_first_post_materializes(
        self,
    ):
        sub = self.paid()
        extra = Patient.objects.create(owner=self.user, name="Berta Demo")
        token = proposal(self.user, sub.plan, "cancel")
        execute(self.user, token, "cancel", selected_patients=[self.patient.pk])
        self.assertEqual(capacity_state(self.user)["count"], 2)
        self.assertTrue(Patient.objects.get(pk=extra.pk).active)
        with patch("CuidadosApp.capacity.timezone.now", return_value=sub.end):
            self.assertEqual(capacity_state(self.user)["active_ids"], [self.patient.pk])
            self.assertTrue(Patient.objects.get(pk=extra.pk).active)
            token = action_token(self.user, self.patient, "posture")
            record_posture(self.user, self.patient.pk, token, self.guide, 60)
            self.assertFalse(Patient.objects.get(pk=extra.pk).active)
            self.assertFalse(CapacitySelection.objects.filter(user=self.user).exists())

    def test_future_selection_update_and_resume_keep_all(self):
        sub = self.paid()
        extra = Patient.objects.create(owner=self.user, name="Berta Demo")
        self.card()
        execute(
            self.user,
            proposal(self.user, sub.plan, "cancel"),
            "cancel",
            selected_patients=[self.patient.pk],
        )
        sub.refresh_from_db()
        choose_capacity(
            self.user,
            [extra.pk],
            [list(row) for row in fingerprint(self.user)],
            sub.version,
            True,
        )
        self.assertEqual(
            CapacitySelection.objects.get(user=self.user).patients, [extra.pk]
        )
        execute(self.user, proposal(self.user, sub.plan, "resume"), "resume")
        self.assertFalse(CapacitySelection.objects.filter(user=self.user).exists())
        self.assertEqual(capacity_state(self.user)["count"], 2)

    def test_expiry_without_selection_keeps_readonly_and_requires_explicit_choice(self):
        sub = self.paid()
        extra = Patient.objects.create(owner=self.user, name="Berta Demo")
        sub.end = self.now - timedelta(seconds=1)
        sub.save()
        self.assertTrue(capacity_state(self.user)["pending"])
        self.assertEqual(capacity_state(self.user)["active_ids"], [])
        with self.assertRaises(ValidationError):
            self.posture()
        response = self.client.get(reverse("CuidadosApp:patient", args=[extra.pk]))
        self.assertContains(response, extra.name)
        choose_capacity(
            self.user,
            [extra.pk],
            [list(row) for row in fingerprint(self.user)],
            sub.version,
        )
        self.assertEqual(capacity_state(self.user)["active_ids"], [extra.pk])
        self.assertFalse(Patient.objects.get(pk=self.patient.pk).active)

    def test_stale_capacity_offer_foreign_ids_and_atomic_rollback(self):
        self.card()
        sub = self.paid()
        extra = Patient.objects.create(owner=self.user, name="Berta Demo")
        free = Plan.objects.get(code="free")
        token = proposal(self.user, free, "purchase")
        with self.assertRaises(ValidationError):
            execute(
                self.user, token, "purchase", free, selected_patients=[self.foreign.pk]
            )
        Patient.objects.filter(pk=extra.pk).update(version=1)
        with self.assertRaises(ValidationError):
            execute(
                self.user, token, "purchase", free, selected_patients=[self.patient.pk]
            )
        token = proposal(self.user, free, "purchase")
        with (
            patch(
                "CuidadosApp.capacity.archive_ids",
                side_effect=DatabaseError("synthetic"),
            ),
            self.assertRaises(DatabaseError),
        ):
            execute(
                self.user, token, "purchase", free, selected_patients=[self.patient.pk]
            )
        sub.refresh_from_db()
        self.assertEqual(sub.plan.code, "plus")
        self.assertEqual(sub.version, 0)
        self.assertEqual(SimulatedOperation.objects.count(), 0)
        self.assertEqual(
            Patient.objects.filter(owner=self.user, active=True).count(), 2
        )

    def test_last_card_retirement_uses_same_selection(self):
        sub = self.paid()
        extra = Patient.objects.create(owner=self.user, name="Berta Demo")
        card = self.card()
        token = proposal(self.user, sub.plan, "cancel")
        with self.assertRaises(ValidationError):
            remove_method(self.user, card, token)
        remove_method(self.user, card, token, [extra.pk])
        self.assertEqual(
            CapacitySelection.objects.get(user=self.user).patients, [extra.pk]
        )
        card.refresh_from_db()
        self.assertFalse(card.active)

    def test_legacy_hogar_preserved_and_not_renewable(self):
        self.card()
        sub = self.paid("hogar")
        self.assertFalse(sub.plan.active)
        self.assertIsNone(capacity_state(self.user)["limit"])
        self.assertEqual(
            self.client.get(reverse("PlanesApp:contratar", args=["hogar"])).status_code,
            404,
        )
        self.assertContains(
            self.client.get(reverse("PlanesApp:mi_suscripcion")), "plan anterior"
        )

    def test_checkout_cancel_and_selection_html_flow(self):
        sub = self.paid()
        extra = Patient.objects.create(owner=self.user, name="Berta Demo")
        self.card()
        response = self.client.get(reverse("PlanesApp:cancelar"))
        self.assertContains(response, self.patient.name)
        self.assertContains(response, extra.name)
        self.assertNotContains(response, self.foreign.name)
        form = response.context["form"]
        response = self.client.post(
            reverse("PlanesApp:cancelar"),
            {"token": form["token"].value(), "patients": [extra.pk]},
        )
        self.assertEqual(response.status_code, 302)
        sub.refresh_from_db()
        self.assertTrue(sub.cancel_at_period_end)
        self.assertEqual(
            CapacitySelection.objects.get(user=self.user).patients, [extra.pk]
        )

    def test_database_constraints_and_guides_assets(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            PostureTimer.objects.create(patient=self.patient, interval=30)
        from django.contrib.staticfiles import finders

        for guide in CareGuide.objects.all():
            self.assertTrue(finders.find(guide.image))
            self.assertTrue(guide.image_alt)
            self.assertTrue(finders.find(guide.illustration["image"]))
            self.assertTrue(guide.illustration["alt"])
            self.assertTrue(guide.source_url.startswith("https://"))
        self.assertEqual(CareGuide.objects.filter(category="posture").count(), 3)


class ConcurrentCapacityTests(TransactionTestCase):
    @skipUnless(
        connection.vendor == "sqlite", "Ensayo de carrera específico de SQLite efímero"
    )
    def test_simultaneous_last_slot_never_exceeds_capacity(self):
        user = User.objects.create_user("carrera_ficticia")
        Plan.objects.update_or_create(
            code="free",
            defaults={
                "name": "VIGIA Free",
                "description": "Prueba",
                "amount_clp": 0,
                "max_active_patients": 1,
            },
        )
        barrier = Barrier(2)

        def both_observe_capacity(actor):
            state = capacity_state(actor)
            barrier.wait(timeout=5)
            return state

        def attempt(index):
            close_old_connections()
            try:
                save_patient(
                    User.objects.get(pk=user.pk), {"name": f"Carrera Demo {index}"}
                )
                return "created"
            except DatabaseError:
                # SQLite refuses one concurrent writer; the view gives a retry
                # message. A backend with row locks instead serializes User.
                return "retry"
            finally:
                connection.close()

        with (
            patch(
                "CuidadosApp.services.capacity_state", side_effect=both_observe_capacity
            ),
            ThreadPoolExecutor(max_workers=2) as executor,
        ):
            outcomes = list(executor.map(attempt, (1, 2)))
        # Shared-cache SQLite can reject BOTH writers upgrading read locks.
        # Verify the bound, then exercise the same user retry the UI requests.
        self.assertLessEqual(outcomes.count("created"), 1)
        self.assertEqual(Patient.objects.filter(owner=user, active=True).count(), outcomes.count("created"))
        if outcomes.count("created") == 0:
            self.assertEqual(outcomes, ["retry", "retry"])
            save_patient(User.objects.get(pk=user.pk), {"name": "Reintento Demo"})
        with self.assertRaises(ValidationError):
            save_patient(User.objects.get(pk=user.pk), {"name": "Cupo excedido"})
        self.assertEqual(Patient.objects.filter(owner=user, active=True).count(), 1)
