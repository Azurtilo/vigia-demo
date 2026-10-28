"""Permisos por paciente. Única fuente de verdad de la lista y de los valores por defecto.

Cada membresía guarda su lista EXPLÍCITA de permisos. Cambiar los valores por defecto aquí
solo afecta a membresías nuevas: nadie gana ni pierde permisos sin una migración decidida.
"""

from typing import Literal, get_args

Permission = Literal[
    "patient.view",  # ver ficha, incluidas alergias y contactos de emergencia
    "patient.edit",  # editar ficha
    "meds.manage",  # crear y editar medicamentos y horarios
    "meds.administer",  # registrar administración (dada / omitida / retrasada)
    "care.manage",  # crear y editar plan de cuidados y tareas
    "care.record",  # confirmar tareas, cambios de posición, observaciones
    "history.view",  # ver historial
    "alerts.handle",  # atender alertas
]

Relation = Literal["owner", "family", "caregiver"]

ALL_PERMISSIONS: tuple[Permission, ...] = get_args(Permission)

DEFAULT_PERMISSIONS: dict[Relation, tuple[Permission, ...]] = {
    "owner": ALL_PERMISSIONS,
    "family": ALL_PERMISSIONS,
    "caregiver": ("patient.view", "meds.administer", "care.record", "history.view", "alerts.handle"),
}

# Acciones exclusivas del dueño: no son permisos delegables.
# - gestionar miembros e invitaciones
# - archivar y reactivar al paciente
