# Modelo de datos (Firestore)

Estado: **aprobado como versión inicial** (2026-10-22). Se detallarán campos obligatorios/opcionales e índices al implementar cada colección.

## Principios

- Las apps no escriben directo en Firestore: todo pasa por FastAPI.
- Datos clínicos en **subcolecciones del paciente**.
- **IDs deterministas** donde hay riesgo de duplicados (membresías, confirmaciones).
- No se almacenan contraseñas (Firebase Auth) ni imágenes/video.

## Colecciones

| Colección | Contenido principal | Notas |
|---|---|---|
| `users/{uid}` | nombre, email, `role` (`admin`/`client`), `status`, `activePatientCount` | Rol y estado solo modificables por backend, con auditoría. Fuente de verdad del rol (ADR 009) |
| `users/{uid}/fcmTokens/{tokenId}` | token, plataforma, última actualización | |
| `patients/{patientId}` | Obligatorios: `ownerUid`, `displayName`, `status` (`active`/`archived`), `timeZone` (IANA, por defecto `America/Santiago`). Opcionales: `birthDate` (texto ISO `AAAA-MM-DD`), `mobility`, `careNeeds`, `notes` (texto libre, sin escalas clínicas), `allergies[]` (≤20), `emergencyContacts[]` (≤3: `name`, `phone`, `relation?`), `activeCameraId`, `createdAt`, `updatedAt` | Minimización de datos. Implementado (Fase 3) |
| `memberships/{patientId}_{uid}` | `patientId`, `uid`, `relation` (`owner`/`family`/`caregiver`), `permissions[]` (lista explícita), `createdAt` | ID compuesto evita duplicados. Consulta "mis pacientes": `uid ==` (índice simple automático). Ver [roles-permisos.md](roles-permisos.md) |
| `invitations/{sha256(código)}` | `patientId`, `email` (minúsculas), `relation` (`family`/`caregiver`), `permissions[]`, `status` (`pending`/`accepted`/`revoked`; `expired` se calcula), `createdBy`, `createdAt`, `expiresAt`, `acceptedBy?`, `acceptedAt?`, `revokedAt?` | El código nunca se guarda: el ID es su huella SHA-256 (ADR 018). Implementado (Fase 3) |
| `patients/{id}/medications/{medId}` | `name`, `dose` (texto tal como fue indicada), `instructions?`, `scheduleType` (`fixed`/`as_needed`), `schedule?` (`times[]` "HH:MM" locales, `daysOfWeek[]` 1-7), `startDate`, `endDate?` (texto ISO), `active`, `createdBy`, `createdAt`, `updatedAt`. Subcolección `revisions/{id}`: `previous` (versión completa), `changedBy`, `changedAt`, `fields[]` | La app no sugiere dosis ni horarios. No se borran: se desactivan. Implementado (Fase 4) |
| `patients/{id}/medicationLogs/{medId}_{AAAAMMDDTHHMMZ}` (programadas) o ID automático ("si es necesario") | `medicationId`, `medicationName` y `dose` (copia de lo indicado al momento), `scheduledAt?`, `agendaAt` (para ubicarla en el día), `status` (`given`/`delayed`/`omitted`), `actualAt?`, `reason?`, `recordedBy`, `recordedAt`, `history[]` (valores reemplazados por correcciones) | ID determinista evita doble confirmación. Consulta de agenda: rango sobre `agendaAt` (índice simple) |
| `patients/{id}/activity/{id}` | `type` (p. ej. `medication.given`), `category` (`medication`/`task`/`position`/`change`), `actorUid`, `occurredAt`, `recordedAt`, `data{}` | Escrito junto con cada acción. Índice compuesto `category` + `occurredAt` DESC (firebase/firestore.indexes.json) |
| `patients/{id}/careTasks/{taskId}` | `title`, `description?`, `kind` (`general`/`position_change`), `scheduleType` (`fixed`/`unscheduled`), `schedule?`, `startDate`, `endDate?`, `assignedTo?` (uid de un miembro), `active`, `createdBy`, `createdAt`, `updatedAt` | Sin frecuencias clínicas predefinidas. Implementado (Fase 4) |
| `patients/{id}/taskLogs/{taskId}_{AAAAMMDDTHHMMZ}` (programadas) o ID automático (sin horario o cambio de posición suelto) | `taskId?` (null = cambio de posición sin tarea), `title` y `kind` (copia), `scheduledAt?`, `agendaAt`, `status` (`done`/`skipped`), `doneAt?`, `reason?`, `note?`, `position?` (`supine`/`left_side`/`right_side`/`prone`/`sitting`/`other`), `positionOther?`, `recordedBy`, `recordedAt`, `history[]` | Mismo esquema anti-duplicados que las tomas |
| `patients/{id}/alerts/{alertId}` | categoría, prioridad, fuente, `dedupKey`, estado, atendida por/cuándo, resultado | |
| `notifications/{id}` | alerta, destinatario, `requested`/`sent`/`failed`, id FCM | Nunca "entregada" sin evidencia |
| `cameras/{cameraId}` | dueño, `patientId`, nombre, tipo/modelo, `status`, `lastSeenAt`, `edgeDeviceId` | 1 cámara activa por paciente (transacción) |
| `edgeDevices/{id}` | dueño, hash de credencial, último contacto | |
| `patients/{id}/postureEvents/{id}` | `mode` (`simulated`/`real`), regla, confianza, timestamp | Solo metadatos |
| `plans/{planId}` (`free`/`plus`/`premium`) | `name`, `order`, `priceClp`, `priceIsTest` (siempre true en el MVP), `available`, `maxPatients` (`null` = ilimitado), `features{}` (ver planes.md), `updatedAt` | Fuente de verdad única; editable solo por admin |
| `subscriptionChanges/{id}` | `uid`, `fromPlan?`, `toPlan`, `changedBy`, `actorRole` (`user`/`admin`), `priceClp` y `priceIsTest` al momento del cambio, `overLimitConfirmed`, `simulated`, `at` | Índice compuesto `uid` + `at` DESC |
| `subscriptions/{uid}` + `subscriptionChanges/{id}` | `planId`, `status`, `simulated: true`, `startedAt`, `updatedAt`; historial de cambios (Fase 5) | Se crea con plan `free` al registrarse. Sin suscripción se aplica Gratis (el más restrictivo) |
| `supportTickets/{id}` | usuario, asunto, estado, respuestas | |
| `auditLogs/{id}` | actor, acción, objetivo, fecha, antes/después sin datos sensibles | |

## Conteo de pacientes activos

- Cuentan los pacientes con `status == active` cuyo `ownerUid` es el usuario.
- Los archivados no cuentan; pueden reactivarse si el plan lo permite.
- Crear o reactivar un paciente ejecuta una **transacción** que lee contador y límite del plan, evitando condiciones de carrera.
- Al bajar de plan no se elimina nada: solo se bloquean nuevas altas mientras se exceda el límite.
