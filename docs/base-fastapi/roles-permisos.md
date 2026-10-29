# Roles y permisos

Estado: **aprobado** (2026-10-25). Implementación: `backend/app/core/permissions.py` (lista y valores por defecto) y `backend/app/services/patients.py` (verificación).

## Autenticación vs. autorización

- **Autenticación** (¿quién eres?): Firebase Authentication emite un ID token; el backend lo verifica con Firebase Admin SDK en cada solicitud.
- **Autorización** (¿qué puedes hacer?): la decide **solo el backend**, con datos de Firestore. Las reglas de Firestore niegan todo acceso directo de la app y el portal.

Orden de verificación en cada operación sobre un paciente:

1. Token válido → si no, **401**.
2. Perfil VIGIA registrado y cuenta activa → si no, **403**.
3. Relación (membresía) con el paciente → si no, **404** (no se revela si el paciente existe).
4. Permiso específico en esa membresía → si no, **403 `forbidden`**.
5. Acción exclusiva del dueño → si no, **403 `owner_only`**.
6. Límite del plan del dueño (altas y reactivaciones) → si se excede, **403 `plan_limit_reached`**.

## Roles de cuenta

| Rol | Cómo se obtiene |
|---|---|
| `client` | Al registrarse (siempre; la API rechaza enviar `role`) |
| `admin` | Solo con `python -m scripts.create_admin <correo>` (acceso de servidor), auditado |

## Relaciones con un paciente y permisos por defecto

Cada membresía (`memberships/{patientId}_{uid}`) guarda su **lista explícita** de permisos. Cambiar los valores por defecto solo afecta a membresías nuevas; aplicarlo a las existentes requiere una migración decidida.

| Permiso | Qué permite | Dueño | Familiar | Cuidador |
|---|---|---|---|---|
| `patient.view` | Ver ficha (incluye alergias y contactos de emergencia) | ✅ | ✅ | ✅ |
| `patient.edit` | Editar ficha | ✅ | ✅ | — |
| `meds.manage` | Crear y editar medicamentos y horarios | ✅ | ✅ | — |
| `meds.administer` | Registrar administración | ✅ | ✅ | ✅ |
| `care.manage` | Crear y editar plan de cuidados y tareas | ✅ | ✅ | — |
| `care.record` | Confirmar tareas, cambios de posición, observaciones | ✅ | ✅ | ✅ |
| `history.view` | Ver historial | ✅ | ✅ | ✅ |
| `alerts.handle` | Atender alertas | ✅ | ✅ | ✅ |

**Solo el dueño** (no delegable): gestionar miembros e invitaciones, archivar y reactivar al paciente.

Motivo de los valores del cuidador: separación de funciones (quien administra no modifica las indicaciones) y mínimo privilegio (los cuidadores rotan más). El dueño puede ampliar los permisos de una persona concreta.

- Cada paciente tiene un único dueño (quien lo registró); su plan determina el límite.
- Los pacientes ajenos a los que alguien tiene acceso no consumen su propio plan.
