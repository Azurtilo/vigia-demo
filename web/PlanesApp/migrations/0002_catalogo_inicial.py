from django.db import migrations

CATALOG = [
    (
        "free",
        "Vigía Free",
        0,
        "Para empezar a vigilar lo esencial",
        [
            "1 cámara conectada",
            "Alertas por correo electrónico",
            "Historial de eventos: 24 horas",
            "Acceso desde la app web",
        ],
    ),
    (
        "plus",
        "Vigía Plus",
        4990,
        "Monitoreo activo para tu día a día",
        [
            "Hasta 3 cámaras conectadas",
            "Notificaciones push instantáneas",
            "Historial de eventos: 7 días",
            "Detección de movimiento",
            "Acceso desde la app web y móvil",
        ],
    ),
    (
        "pro",
        "Vigía Pro",
        9990,
        "Vigilancia sin límites, con prioridad",
        [
            "Cámaras conectadas ilimitadas",
            "Notificaciones push + SMS",
            "Historial de eventos: 30 días",
            "Detección de personas y vehículos",
            "Soporte prioritario 24/7",
        ],
    ),
    (
        "hogar",
        "Vigía Hogar",
        14990,
        "Toda la familia, una sola torre de vigilancia",
        [
            "Todo lo incluido en Vigía Pro",
            "Hasta 5 perfiles familiares",
            "Almacenamiento en la nube: 60 días",
            "Panel de control compartido",
            "Soporte prioritario 24/7",
        ],
    ),
]


def seed(apps, schema_editor):
    alias = schema_editor.connection.alias
    Position = apps.get_model("UsuarioApp", "Position")
    position, _ = Position.objects.using(alias).get_or_create(
        user_position="Cliente público", defaults={"permission_code": "RESTRICTED"}
    )
    if position.permission_code != "RESTRICTED":
        raise RuntimeError(
            "El nombre Cliente público ya está ocupado por otro código de cargo. No se modificó ese cargo."
        )
    Plan = apps.get_model("PlanesApp", "Plan")
    Benefit = apps.get_model("PlanesApp", "PlanBenefit")
    for order, (code, name, amount, description, benefits) in enumerate(CATALOG):
        plan, created = Plan.objects.using(alias).get_or_create(
            code=code,
            defaults={
                "name": name,
                "amount_clp": amount,
                "description": description,
                "display_order": order,
            },
        )
        if created:
            for index, text in enumerate(benefits):
                Benefit.objects.using(alias).create(plan=plan, text=text, order=index)


class Migration(migrations.Migration):
    dependencies = [
        ("PlanesApp", "0001_initial"),
        ("UsuarioApp", "0002_user_visual_preference"),
    ]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
