"""Carga los planes Gratis, Plus y Premium en Firestore (precios de PRUEBA).

No sobrescribe planes existentes salvo con --overwrite (pueden haber sido editados en el portal).
Con los emuladores hay que ejecutarlo cada vez que se inician, porque sus datos se borran al cerrarlos.

Uso (desde backend/, con el entorno virtual activo):
    python -m scripts.seed_plans
"""

import argparse

from app.core.config import get_settings
from app.services.plans import DEFAULT_PLANS, seed_plans


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga los planes por defecto en Firestore.")
    parser.add_argument("--overwrite", action="store_true", help="Reemplazar planes ya existentes")
    args = parser.parse_args()

    settings = get_settings()
    target = "EMULADOR LOCAL" if settings.uses_emulators else "FIREBASE REAL"
    print(f"Proyecto: {settings.firebase_project_id} ({target})")

    written = seed_plans(overwrite=args.overwrite)
    skipped = [p for p in DEFAULT_PLANS if p not in written]
    print(f"Planes escritos: {', '.join(written) or 'ninguno'}")
    if skipped:
        print(f"Ya existían (sin cambios): {', '.join(skipped)}")


if __name__ == "__main__":
    main()
