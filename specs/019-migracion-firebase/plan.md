# Plan técnico — 019 / Migración a FastAPI + Firebase

Spec: [spec.md](spec.md). Estado: aprobado con la spec (2026-10-28).
Autorización de implementación: SÍ, por tareas (ver [tasks.md](tasks.md)); sin merge, despliegue ni cuentas reales.

## Inspección de la base

- **Este repositorio** (`origin/develop`, `73fb6a1`): Django en `web/` con la API móvil y del nodo en `web/CuidadosApp/api/` (`views.py`, `detection.py`, `access.py`, `devices.py`), push en `CuidadosApp/push.py`, recordatorios en el comando `send_mobile_reminders`, consentimiento en `PrivacidadApp/consent.py` y planes en `PlanesApp/entitlements.py`. App en `mobile/lib` (estado con `setState`, mapas sin tipo, 6 pestañas). Edge en `edge/` (renueva cada 10 s, `edge/run.py:26`).
- **Proyecto base** (`C:\Users\josea\Downloads\vigia 26 - copia\vigia 26 - copia`, commit `518792263c44`, 2026-10-28, solo lectura):
  - `backend/app`: unas 3.400 líneas (users, patients, members e invitaciones, medications, care, agenda, history, subscriptions, admin) y 2.300 de pruebas con emuladores.
  - `mobile/lib`: unas 6.000 líneas con Riverpod, go_router, dio y Firebase Auth; la sección Alertas es un marcador de posición.
  - `web/src`: portal React, solo el esqueleto.
  - `firebase/`: reglas que niegan el acceso directo, índices y prueba de reglas.
  - `docs/`: arquitectura, ADR 001–027, modelo de datos, planes, roles y diseño visual.
- **No se copian:** `backend/.env`, `.venv`, `.pytest_cache`, `mobile/build`, `.dart_tool`, `.idea`, `firestore-debug.log` ni `web/dist`.
- **Entorno de este equipo:** Python 3.12.4. Sin Java ni Node (P-019-01).

## Estructura del repositorio en la rama

| Ruta | Contenido |
|---|---|
| `backend/` | FastAPI importado y ampliado (nuevo) |
| `firebase/`, `firebase.json`, `.firebaserc` | Reglas, índices y emuladores (`demo-vigia`) (nuevo) |
| `portal/` | Portal React (su `web/` renombrado para no chocar con Django) (nuevo) |
| `mobile/` | Se conservan `android/`, `ios/`, `plugins/vigia_pose`, `assets/` y el identificador; `lib/` y `test/` pasan a la estructura del proyecto base más nuestras funciones |
| `edge/` | Sin cambios |
| `web/` | Django sin cambios hasta la fusión |
| `docs/base-fastapi/` | Documentos del proyecto base (ADR, modelo, planes, roles, diseño), como antecedente citado |

## Diseño del backend

Módulos nuevos, con el mismo estilo del proyecto base (`api/v1/*.py` delgados, reglas en `services/*.py` y modelos Pydantic en `models/*.py`):

| Pieza | Origen en Django | Destino |
|---|---|---|
| Nodos: vincular, listar, revocar | `api/detection.py` `NodesView`, `RevokeNodeView` | `api/v1/nodes.py`, `services/nodes.py` |
| Contrato Edge | `api/detection.py` `EdgeView` | `api/edge.py` montado en **`/api/v1/edge`** (ruta idéntica a la de hoy; el resto de la API sigue en `/v1`) |
| Observaciones y teléfono | `ObservationsView`, `PhoneObservationsView` | `services/observations.py` |
| Alertas y push | `push.py`, `send_mobile_reminders` | `services/alerts.py`, `services/push.py` (FCM con Admin SDK) |
| Estado de cámara (D-073..D-077) | `camera_state`, `node_data` | `services/nodes.py` |
| Reloj de posición | `TimerView`, `TimerScheduleView` | `api/v1/timer.py`; el registro de cambio de posición existente lo reinicia |
| Consentimiento | `PrivacidadApp/consent.py` | `api/v1/consent.py`, `services/consent.py` |
| Dispositivos FCM | `api/devices.py` | `api/v1/devices.py` |
| Tick del cron | `send_mobile_reminders` | `api/internal.py` `POST /internal/tick` con cabecera `X-Cron-Secret` (comparación en tiempo constante) |
| Purga, exportación y eliminación (D-098) | `PrivacidadApp/retention.py`, `export.py`, `erase.py`, `purge_expired_data` | `services/retention.py` (la llama el tick una vez al día, marcada en `privacyOperations`), `services/export.py`, `services/erase.py`, `api/v1/privacy.py` |

**Autorización del nodo (D-086):** al vincular se generan `secrets.token_urlsafe(32)` y su SHA-256, y se crea `edgeNodes/{nodeId}` con `credentialHash`. En cada solicitud se busca por igualdad sobre el hash. Las reglas de 403 son las mismas de `allowed()`: plan del dueño con cámara, paciente dentro de la capacidad, consentimiento de detección y nodo activo.

**Cuota de Firestore (D-095):**

| Tráfico de 1 nodo al día | Sin caché | Con caché |
|---|---|---|
| Renovaciones (cada 10 s = 8.640) | ~5 lecturas + 1 escritura cada una ≈ 43.000 L / 8.640 E | Autorización en memoria 60 s ≈ 7.200 L; última señal cada 30 s ≈ 2.880 E |
| Límite de Spark | 50.000 L / 20.000 E | Margen para 3 teléfonos y observaciones |

La caché vive en el proceso (un solo proceso en Render, supuesto de la spec) y se invalida en ese mismo proceso al revocar el nodo, cambiar el plan o revocar el consentimiento. Una prueba de presupuesto cuenta las lecturas y escrituras con un Firestore simulado.

**Recordatorios (D-088, D-089):** cada tick busca las tomas programadas de los últimos 5 minutos sin registro y crea `reminderDeliveries/{patientId}_{medId}_{instanteUTC}` con `create()`. Si el documento ya existe, no se envía nada; eso evita duplicados entre ticks. También revisa los nodos sin señal por más de 60 s. La app programa los avisos locales con el mismo identificador.

## Diseño de la app

- Se toma `lib/` del proyecto base (core: config, red, router y tema; features: auth, patients, today, care, history, members y account) y se integran nuestras funciones como features:
  - `features/detection` ← `phone_pose*.dart` y `pose_classifier.dart`.
  - `features/posture` ← `clock_panel.dart` y `posture_hub.dart`.
  - `features/nodes` ← la tarjeta del nodo y `camera_state.dart`.
  - `features/alerts` (nueva).
  - `features/notifications` ← `local_reminders.dart` más FCM.
  - `features/privacy` ← `privacy.dart`.
- **Dependencias:** se suman las nuestras (`camera`, `vigia_pose`, `flutter_local_notifications`, `timezone`, `firebase_messaging`, `url_launcher`, `google_sign_in`) a las del base. `firebase_core` debe quedar en una sola versión mayor compatible con `firebase_auth` y `firebase_messaging` (hoy el base usa la 5 y nosotros la 4); se resuelve en T-019-08.
- **Navegación:** 5 ramas en `StatefulShellRoute` (Hoy, Pacientes, Alertas, Posturas y Cuenta).
- **Recarga:** se elimina el `Timer.periodic` de 60 s. Se refresca al abrir, al volver a primer plano, al llegar un push y como máximo cada 5 minutos (RF-019-19).

## Portal

Se copia `portal/` (Vite + React + TypeScript). Pantallas: ingreso (Firebase Auth), mi plan y cambio simulado usando `GET /v1/me/subscription/preview` y `POST /v1/me/subscription/change`. Sin la paleta nueva (D-093).

## Operación (D-084, D-091)

- **Render (servicio web, plan gratis):** `uvicorn app.main:app`. Variables: `VIGIA_ENVIRONMENT=production`, `VIGIA_FIREBASE_PROJECT_ID`, credenciales de la cuenta de servicio en una variable secreta y `VIGIA_CRON_SECRET`.
- **cron-job.org:** `POST /internal/tick` cada minuto con la cabecera secreta. Además mantiene el servicio despierto.
- **Firebase Spark:** Auth (correo y Google), Firestore con `firebase deploy --only firestore` (reglas e índices) y FCM.

## Diferencias de reglas a confirmar (P-019-02)

Por defecto se adopta la regla del proyecto base; el propietario puede cambiar cada una antes de T-019-04.

| # | Tema | Este repositorio (Django) | Proyecto base | Por defecto |
|---|---|---|---|---|
| 1 | Unirse a un paciente | Código de la 013 con vista previa y aceptación | Código de 20 caracteres, 7 días, **exige el mismo correo invitado** | Base, conservando la vista previa de la 013 |
| 2 | Estados de toma | Realizada / omitida con motivo | A tiempo / con retraso con hora real / no dada con motivo, más correcciones | Base (D-087) |
| 3 | Historial por plan | Sin límite por plan | 30 / 365 / sin límite días visibles | Base |
| 4 | Conservación y purga (014) | Plazos y purga diaria | No borra nunca | **Se porta (D-098):** RF-019-24, purga diaria desde el tick. El archivado del base se conserva y los archivados se purgan a los 2 años |
| 5 | Exportar datos y eliminar cuenta (014) | Implementados | No existen | **Se porta (D-098):** RF-019-25..27. Para eliminar, se reautentica con el `auth_time` del token de Firebase en lugar de la contraseña |
| 6 | Planes y precios | Planes de PlanesApp | Gratis / Plus $4.990 / Premium $9.990 (prueba) | Base |
| 7 | Guías de cuidado postural | Endpoint `guides` | No existen | Se sirven desde los assets de la app, sin backend |
| 8 | Detección y cupo del plan (encontrada en T-019-04) | El paciente debe estar dentro del cupo activo del plan (`capacity_state`) | Al bajar de plan no se elige qué pacientes quedan; solo se bloquean altas | Base: la detección exige cámara en el plan del dueño (solo Premium, que no tiene límite de pacientes), paciente activo y consentimiento. Sin cupo por paciente |
| 9 | Permisos de detección (T-019-04) | `manage_nodes` (titular) y `detection` | Sin permisos de detección | Nodos: solo el dueño. Observaciones: `alerts.handle`. Teléfono: `care.record`. Estado de la cámara: `patient.view` |

## Plan de pruebas

- **Backend:** `pytest` del base más pruebas nuevas por RF: contrato Edge (cada validación de `EdgeView` con su caso), deduplicación, 401/403, push con FCM simulado, tick sin y con secreto, idempotencia de recordatorios, consentimiento fail-closed, presupuesto de Firestore y matriz por rol.
- **Edge:** `python -m unittest edge.test_posture edge.test_fall edge.test_run` sin cambios. Además, una prueba de humo contra el backend local con emuladores.
- **App:** `flutter analyze` y `flutter test` (las pruebas del base más las nuestras portadas a Riverpod).
- **Manual:** punto de control de la semana 1 (nodo real → push en Android) y recorrido de las HU-01..07 en Android físico. Los resultados van en `validation.md`.

## Migraciones y reversión

No hay migración de datos (D-085). La reversión es volver a `develop` (Django), que no se toca. Si el proyecto Firebase real se crea, sus datos de piloto se pueden borrar sin afectar a Django.

## Riesgos, alternativas y dependencias

- **Calendario de 3 semanas.** Si el punto de control del 2026-11-04 falla, se recomienda entregar con Django (D-081).
- **Sin Java ni Node no corren las pruebas del backend (P-019-01).** Mientras tanto se avanza con las pruebas unitarias que no usan emuladores y se declara lo omitido.
- **Versiones de FlutterFire** entre el base y nuestras dependencias (T-019-08).
- **Render gratis:** puede cambiar sus condiciones; alternativa: Koyeb u otro servicio sin tarjeta.
- **Regresión de cumplimiento** por las diferencias 4 y 5.

## Calendario

| Semana | Tareas |
|---|---|
| 1 (al 2026-11-04) | T-019-01..07: documentos, importación, herramientas, contrato Edge, alertas y push, consentimiento, tick, despliegue de prueba y punto de control |
| 2 (al 2026-11-11) | T-019-08..12: app con base importada y nuestras funciones; T-019-16: privacidad en el backend |
| 3 (al 2026-11-18) | T-019-13..15: portal mínimo, revalidación y documentos |

## Documentos afectados

`AGENTS.md` y `CLAUDE.md` (en la rama), `specs/README.md`, `docs/DECISIONES.md` (D-081..D-097), `docs/ESTADO_PROYECTO.md`, `docs/TRAZABILIDAD.md` (al validar), `docs/ARQUITECTURA_BASE.md` (al cierre) y `README.md`.

## Decisiones para implementar

P-019-01 y las diferencias 4 y 5 de P-019-02 se resolvieron el 2026-10-28 (D-098, D-099). Queda P-019-03 (D-100), que solo bloquea T-019-07.
