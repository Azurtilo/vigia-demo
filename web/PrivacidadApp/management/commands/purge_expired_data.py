"""Delete data past its retention period (D-064). Reports counts only."""

from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from CuidadosApp.models import Patient
from PlanesApp.services import locked_user
from PrivacidadApp.erase import erase_patient_rows
from PrivacidadApp.models import PrivacyOperation
from PrivacidadApp.retention import RETENTION, expired


class Command(BaseCommand):
    help = "Purga los datos vencidos según los plazos de conservación aprobados."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Solo cuenta; no borra nada."
        )

    def handle(self, *args, dry_run=False, **options):
        now = timezone.now()
        counts = {}
        for key, rows in expired(now).items():
            if dry_run:
                counts[key] = rows.count()
            else:
                with transaction.atomic():
                    counts[key] = rows.delete()[0]
        archived = Patient.objects.filter(
            active=False, archived_at__lt=now - RETENTION["archived_patients"]
        )
        counts["archived_patients"] = archived.count()
        if not dry_run:
            for pk in list(archived.values_list("pk", flat=True)):
                with transaction.atomic():
                    patient = Patient.objects.select_related("owner").get(pk=pk)
                    if patient.owner.is_active:  # same lock as care actions
                        locked_user(patient.owner)
                    erase_patient_rows(patient)
        counts["expired_sessions"] = Session.objects.filter(expire_date__lt=now).count()
        if not dry_run:
            Session.objects.filter(expire_date__lt=now).delete()
            PrivacyOperation.objects.create(kind="purge", counts=counts)
        mode = "Simulación (sin borrar)" if dry_run else "Purga realizada"
        self.stdout.write(f"{mode}: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
