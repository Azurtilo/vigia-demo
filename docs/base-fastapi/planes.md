# Planes y reglas de negocio

Estado: **aprobado** (2026-10-22). Los valores se cargarán en la colección `plans` (fuente de verdad única) y serán editables desde el portal administrativo.

| Función | Gratis | Plus | Premium |
|---|---|---|---|
| Pacientes activos | 1 | 3 | Ilimitados |
| Ficha, medicamentos, horarios, recordatorios básicos | ✅ | ✅ | ✅ |
| Tareas de cuidado básicas, registros esenciales | ✅ | ✅ | ✅ |
| Consejos generales de cuidado postural | ✅ | ✅ | ✅ |
| Seguimiento ampliado de tareas, registro de cambios de posición | — | ✅ | ✅ |
| Historial de cuidados y actividades (visible) * | Últimos 30 días | 12 meses | Completo |
| Informe exportable (PDF) * | — | ✅ | ✅ (ampliado) |
| Cámara vinculada (1 por paciente) + análisis de postura | — | — | ✅ (experimental) |
| Alertas avanzadas de monitoreo | — | — | ✅ (sujeto a validación) |
| Precio | $0 | **PRUEBA** $4.990 CLP/mes | **PRUEBA** $9.990 CLP/mes |

\* Funciones propuestas durante la planificación y aprobadas.

## Reglas

- El límite del historial afecta solo **lo que se muestra**; los datos se conservan completos.
- Los precios son **valores de prueba**, no comerciales. No hay cobros reales en el MVP: suscripciones y cambios de plan son simulados y quedan registrados.
- Los límites se aplican en el backend (transacción) y se reflejan en la interfaz con el motivo del bloqueo.
- Invitar cuidadores o familiares está disponible en todos los planes, sin límite por plan.
- **Siempre aplica el plan del dueño del paciente**, también para familiares y cuidadores que tengan otro plan.

## Definición de las funciones (aprobada 2026-10-25)

| Clave en `plans.features` | Qué habilita | Gratis | Plus | Premium |
|---|---|---|---|---|
| (siempre) | Medicamentos, horarios, registro de tomas; crear tareas y marcarlas realizadas | ✅ | ✅ | ✅ |
| `extendedCareTracking` | Asignar responsable a una tarea, marcarla "no realizada" con motivo, agregar observaciones | — | ✅ | ✅ |
| `positionChanges` | Tareas de cambio de posición y registro de posiciones | — | ✅ | ✅ |
| `historyDays` | Días de historial visibles (30 / 365 / sin límite) | 30 | 365 | ∞ |

Al bajar de plan, lo ya creado se conserva (tareas asignadas, registros); solo se bloquean las acciones que el nuevo plan no incluye.

## Cambios de plan (implementado en la Fase 5)

- `GET /v1/me/subscription/preview?planId=…` simula el cambio sin aplicarlo (precio, límite, funciones que se perderían).
- `POST /v1/me/subscription/change`: subir es inmediato; bajar quedando sobre el límite exige `confirmOverLimit: true`.
- Cada cambio queda en `subscriptionChanges` (con el precio de prueba vigente en ese momento) y en `auditLogs`.

## Administración de planes (solo rol admin)

- Siempre los mismos tres planes: se editan nombre, precio de prueba, límite de pacientes, funciones y disponibilidad.
- Gratis: precio $0 y siempre disponible. `priceIsTest` no es editable en el MVP.
- Un plan no disponible lo conserva quien ya lo tiene, pero no se puede elegir. Un admin sí puede asignarlo.
- Bajar el límite o quitar funciones no borra datos de nadie.
