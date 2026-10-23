from django.db import migrations


CATALOG = [
    ("free", "VIGIA Free", 0, 1, "Organiza el cuidado de una persona"),
    ("plus", "VIGIA Plus", 4990, 3, "Acompaña hasta tres pacientes"),
    ("pro", "VIGIA Premium", 9990, None, "Todos tus pacientes, en un mismo espacio"),
]


def forward(apps, schema_editor):
    alias = schema_editor.connection.alias
    Plan = apps.get_model("PlanesApp", "Plan")
    Benefit = apps.get_model("PlanesApp", "PlanBenefit")
    for plan in Plan.objects.using(alias).filter(
        code__in=["free", "plus", "pro", "hogar"]
    ):
        plan.catalog_before_care = {
            "name": plan.name,
            "amount_clp": plan.amount_clp,
            "description": plan.description,
            "active": plan.active,
            "max_active_patients": plan.max_active_patients,
            "benefits": list(
                Benefit.objects.using(alias).filter(plan=plan).values("text", "order")
            ),
        }
        plan.max_active_patients = None
        if plan.code == "hogar":
            plan.active = False
        else:
            (
                _,
                plan.name,
                plan.amount_clp,
                plan.max_active_patients,
                plan.description,
            ) = next(row for row in CATALOG if row[0] == plan.code)
            plan.active = True
            Benefit.objects.using(alias).filter(plan=plan).delete()
            benefits = [
                "1 paciente activo"
                if plan.code == "free"
                else "Hasta 3 pacientes activos"
                if plan.code == "plus"
                else "Pacientes activos ilimitados",
                "Ficha y contacto de emergencia",
                "Medicamentos, horarios y agenda",
                "Guías visuales y registro de posturas",
                "Recordatorios con la web abierta e historial",
            ]
            if plan.code == "pro":
                benefits.append("IA y cámaras · Próximamente")
            for order, text in enumerate(benefits):
                Benefit.objects.using(alias).create(plan=plan, text=text, order=order)
        plan.save(using=alias)


def backward(apps, schema_editor):
    alias = schema_editor.connection.alias
    Plan = apps.get_model("PlanesApp", "Plan")
    Benefit = apps.get_model("PlanesApp", "PlanBenefit")
    for plan in Plan.objects.using(alias).exclude(catalog_before_care={}):
        values = dict(plan.catalog_before_care)
        benefits = values.pop("benefits")
        for field, value in values.items():
            setattr(plan, field, value)
        plan.catalog_before_care = {}
        plan.save(using=alias)
        Benefit.objects.using(alias).filter(plan=plan).delete()
        for benefit in benefits:
            Benefit.objects.using(alias).create(plan=plan, **benefit)


class Migration(migrations.Migration):
    dependencies = [
        ("PlanesApp", "0003_plan_catalog_before_care_plan_max_active_patients_and_more")
    ]
    operations = [migrations.RunPython(forward, backward)]
