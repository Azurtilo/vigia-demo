from datetime import time, timedelta

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from CuidadosApp.models import CareTask, Medication, MedicationTime, Patient
from PlanesApp.models import Plan, Subscription
from UsuarioApp.services import provision_public_user


class Command(BaseCommand):
    help = "Create fictitious demo accounts, exclusively in mobile_demo_settings."

    @transaction.atomic
    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != "core.mobile_demo_settings":
            raise CommandError(
                "Solo permitido con --settings=core.mobile_demo_settings."
            )
        for code, username, name in [
            ("free", "demo_free", "Elena Demo"),
            ("plus", "demo_plus", "Mateo Demo"),
            ("pro", "demo_premium", "Rosa Demo"),
        ]:
            user, created = User.objects.get_or_create(
                username=username, defaults={"email": f"{username}@example.test"}
            )
            if not created:
                continue  # Never overwrite an existing password or changed data.
            user.set_password("VigiaDemo-2026!")
            user.save()
            provision_public_user(user)
            EmailAddress.objects.update_or_create(
                user=user,
                email=user.email,
                defaults={"verified": True, "primary": True},
            )
            plan = Plan.objects.get(code=code)
            Subscription.objects.update_or_create(
                user=user,
                defaults={
                    "plan": plan,
                    "plan_name": plan.name,
                    "amount_clp": plan.amount_clp,
                    "start": timezone.now() - timedelta(days=1)
                    if code != "free"
                    else None,
                    "end": timezone.now() + timedelta(days=29)
                    if code != "free"
                    else None,
                },
            )
            p = Patient.objects.create(
                owner=user,
                name=name,
                notes="Datos ficticios para probar VIGIA.",
                contact_name="Contacto Demo",
                contact_phone="+56 9 0000 0000",
                contact_relation="Familiar",
            )
            m = Medication.objects.create(
                patient=p,
                name="Medicación de ejemplo",
                dose="Según indicación registrada",
                schedule_effective_at=timezone.now() - timedelta(hours=12),
            )
            MedicationTime.objects.create(medication=m, time=time(8))
            MedicationTime.objects.create(medication=m, time=time(20))
            CareTask.objects.create(
                patient=p,
                name="Revisar comodidad e higiene",
                notes="Actividad ficticia de demostración.",
            )
        self.stdout.write(
            "Cuentas ficticias listas: demo_free, demo_plus, demo_premium. Contraseña local: VigiaDemo-2026!"
        )
