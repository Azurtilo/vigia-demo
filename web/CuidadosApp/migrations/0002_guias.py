from django.db import migrations


GUIDES = [
    ("supina", "Decúbito supino", "posture", [
        "La persona descansa boca arriba; sigue el posicionamiento indicado en su plan de cuidados.",
        "Comprueba comodidad y apoyos; observa las zonas de contacto y registra el cambio realizado.",
    ], "Vista superior de una persona boca arriba sobre una cama, con apoyos de referencia."),
    ("lateral-izquierda", "Decúbito lateral izquierdo", "posture", [
        "La persona descansa sobre su lado izquierdo, con apoyos según su plan de cuidados.",
        "Comprueba alineación y comodidad; evita presión entre las rodillas y registra la postura realizada.",
    ], "Persona sobre su lado izquierdo; apoyo detrás del tronco y entre las rodillas."),
    ("lateral-derecha", "Decúbito lateral derecho", "posture", [
        "La persona descansa sobre su lado derecho, con apoyos según su plan de cuidados.",
        "Comprueba comodidad y apoyos; registra el cambio y el intervalo acordado.",
    ], "Persona sobre su lado derecho; apoyo detrás del tronco y entre las rodillas."),
    ("comodidad", "Comodidad y preparación", "care", [
        "Explica el cuidado y pregunta por dolor o incomodidad.",
        "Revisa que no haya objetos bajo la persona; usa ayuda y equipos de movilización apropiados.",
    ], "Cama preparada con almohada y apoyos; lista visual de comodidad y cuidado."),
]


def seed(apps, schema_editor):
    Guide = apps.get_model("CuidadosApp", "CareGuide")
    for code, title, category, instructions, alt in GUIDES:
        Guide.objects.using(schema_editor.connection.alias).get_or_create(code=code, defaults={
            "title": title, "category": category, "instructions": instructions,
            "precautions": "Referencia educativa. Sigue el plan individual de cuidados y la técnica enseñada por el equipo de salud.",
            "image": f"CuidadosApp/guides/{code}.svg", "image_alt": alt,
            "source_url": "https://www.internationalguideline.com/repositioning",
            "source_title": "International Guideline · Repositioning (2026)",
        })


def unseed(apps, schema_editor):
    apps.get_model("CuidadosApp", "CareGuide").objects.using(schema_editor.connection.alias).filter(code__in=[row[0] for row in GUIDES]).delete()


class Migration(migrations.Migration):
    dependencies = [("CuidadosApp", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
