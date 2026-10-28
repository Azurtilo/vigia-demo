# Tareas — 019 / Migración a FastAPI + Firebase

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md).
Estado: T-019-01 y T-019-02 hechas; el resto, pendientes. Implementación autorizada: SÍ, T-019-01..15 (2026-10-28), sin merge, despliegue ni cuentas reales; cada una de esas acciones necesita autorización aparte.
Rama: `feature/019-migracion-firebase` desde `origin/develop` (`73fb6a1`), un commit por tarea y PR hacia `develop` (D-059).

## Semana 1 — backend (punto de control 2026-11-04)

- [x] T-019-01 — Documentos y registro de decisiones.
  - RF: todos.
  - Depende de: autorización.
  - Archivos previstos: `specs/019-migracion-firebase/*`, `specs/README.md`, `docs/DECISIONES.md` (D-081..D-097), `docs/ESTADO_PROYECTO.md`, `AGENTS.md` y `CLAUDE.md` (D-083).
  - Hecho cuando: spec, plan y tareas están en la rama; las decisiones citan la fuente; AGENTS y CLAUDE describen el backend FastAPI de esta rama sin borrar las reglas de Django que siguen vigentes en `develop`.
- [x] T-019-02 — Importar el proyecto base.
  - RF: RF-019-01, RF-019-20 (solo copia).
  - Depende de: T-019-01.
  - Archivos previstos: `backend/`, `firebase/`, `firebase.json`, `.firebaserc`, `portal/` (desde `web/` del base), `docs/base-fastapi/`, `.gitignore`.
  - Hecho cuando: los archivos están copiados desde el commit `518792263c44`, sin `.env`, entornos, cachés ni compilados. Las pruebas del backend que no usan emuladores pasan y las demás aparecen como omitidas, con el conteo registrado.
- [ ] T-019-03 — Herramientas y emuladores.
  - RF: RF-019-01.
  - Depende de: T-019-02 y D-099 (instalación de JDK 21, Node LTS y `firebase-tools` con `winget`, autorizada).
  - Archivos previstos: `docs/ENTORNO_Y_VERIFICACION.md`, `.venv-backend` (local, no versionado).
  - Hecho cuando: `firebase emulators:start` funciona y la suite completa del backend pasa sin omisiones.
- [ ] T-019-04 — Nodos y contrato Edge.
  - RF: RF-019-02, RF-019-03, RF-019-05, RF-019-10, RF-019-11, RF-019-22.
  - Depende de: T-019-02 (T-019-03 para correr la integración).
  - Archivos previstos: `backend/app/api/edge.py`, `api/v1/nodes.py`, `services/nodes.py`, `services/observations.py`, `models/nodes.py`, `firebase/firestore.indexes.json`, pruebas.
  - Hecho cuando: cada caso de `EdgeView` y `PhoneObservationsView` tiene su prueba, más la caché invalidada al revocar y la prueba de presupuesto. `edge.test_*` pasan sin cambios.
- [ ] T-019-05 — Alertas y push.
  - RF: RF-019-04, RF-019-05, RF-019-09.
  - Depende de: T-019-04.
  - Archivos previstos: `services/alerts.py`, `services/push.py`, `api/v1/alerts.py`, `api/v1/devices.py`, pruebas con FCM simulado.
  - Hecho cuando: una caída crea la alerta y solicita el push solo a los destinatarios con permiso y plan; los avisos de cámara salen una vez por episodio; el texto no contiene datos clínicos.
- [ ] T-019-06 — Consentimiento, reloj y tick del cron.
  - RF: RF-019-06, RF-019-07, RF-019-08.
  - Depende de: T-019-04.
  - Archivos previstos: `api/v1/consent.py`, `services/consent.py`, `api/v1/timer.py`, `api/internal.py`, `services/reminders.py`, pruebas.
  - Hecho cuando: sin consentimiento de detección el nodo recibe 403; el cambio de posición reinicia el reloj; el tick sin secreto da 401 y dos ticks seguidos envían un solo recordatorio por toma.
- [ ] T-019-07 — Despliegue de prueba y punto de control.
  - RF: RF-019-21, RF-019-22.
  - Depende de: T-019-05, T-019-06 y P-019-03, **pendiente por D-100** (cuentas del propietario). Para el punto de control basta el proyecto Firebase, con el backend en este PC; Render y el cron pueden esperar. **El despliegue requiere autorización aparte.**
  - Archivos previstos: `docs/OPERACION.md`, `render.yaml` si corresponde, `validation.md`.
  - Hecho cuando: el nodo real envía una caída, el push llega a un Android y la demora queda medida. Si no ocurre al 2026-11-04, se informa al propietario (D-081).

## Semana 2 — app móvil

- [ ] T-019-08 — Base de la app dentro de `mobile/`.
  - RF: RF-019-12, RF-019-18.
  - Depende de: T-019-02.
  - Archivos previstos: `mobile/lib/**`, `mobile/test/**`, `mobile/pubspec.yaml`, `mobile/assets/branding`, `mobile/assets/fonts`.
  - Hecho cuando: la app del base compila con nuestro identificador, plugin y assets; las versiones de FlutterFire son compatibles entre sí; `flutter analyze` está limpio y `flutter test` pasa.
- [ ] T-019-09 — Cinco secciones y Alertas.
  - RF: RF-019-13, RF-019-14.
  - Depende de: T-019-08 y T-019-05.
  - Hecho cuando: hay pruebas de navegación y de la lista de alertas, y las 5 etiquetas caben a 360 dp.
- [ ] T-019-10 — Posturas: teléfono, reloj y nodo.
  - RF: RF-019-15.
  - Depende de: T-019-08, T-019-04 y T-019-06.
  - Hecho cuando: las pruebas portadas de `clock_panel`, `camera_state` y `pose_classifier` pasan con los nuevos proveedores de datos.
- [ ] T-019-11 — Push y recordatorios locales de respaldo.
  - RF: RF-019-16, RF-019-19.
  - Depende de: T-019-08 y T-019-06.
  - Hecho cuando: las pruebas cubren el mismo identificador de toma, la cancelación al registrar y la recarga sin temporizador de 60 s.
- [ ] T-019-12 — Política y consentimiento en la app.
  - RF: RF-019-17.
  - Depende de: T-019-08 y T-019-06.
  - Hecho cuando: las pruebas portadas de `privacy_test` y `login_consent_test` pasan.

- [ ] T-019-16 — Privacidad en el backend: purga, exportación y eliminación (D-098).
  - RF: RF-019-24, RF-019-25, RF-019-26, RF-019-27.
  - Depende de: T-019-06 (tick y consentimiento).
  - Archivos previstos: `services/retention.py`, `services/export.py`, `services/erase.py`, `api/v1/privacy.py`, pruebas; pantallas de exportar y eliminar en la app (T-019-12) y en el portal (T-019-13).
  - Hecho cuando: hay pruebas de cada plazo (justo antes y después del límite), de que la exportación no lleva tokens, hashes ni códigos, del borrado completo del paciente, y del rechazo de la eliminación de cuenta sin inicio de sesión reciente, con autor anónimo en pacientes ajenos.

## Semana 3 — portal, validación y cierre

- [ ] T-019-13 — Portal mínimo de suscripción.
  - RF: RF-019-20.
  - Depende de: T-019-02 y T-019-03 (Node).
  - Hecho cuando: ingreso, ver plan y cambio simulado funcionan contra los emuladores; las pruebas del portal y el build pasan.
- [ ] T-019-14 — Revalidación.
  - RF: RF-019-23.
  - Depende de: T-019-07..13.
  - Archivos previstos: `specs/019-migracion-firebase/validation.md`, `docs/TRAZABILIDAD.md`.
  - Hecho cuando: cada HU, RT y RNF tiene evidencia nueva o queda marcada «sin evidencia», con los comandos y resultados reales.
- [ ] T-019-15 — Cierre documental.
  - RF: todos.
  - Depende de: T-019-14.
  - Archivos previstos: `README.md`, `docs/ARQUITECTURA_BASE.md`, `docs/ESTADO_PROYECTO.md`, `specs/README.md`.
  - Hecho cuando: los documentos describen la arquitectura de la rama, la PR está abierta y el merge queda pendiente de autorización.

## Autorización posterior

«concuerdo con tus decisiones, dejamos develop con django y probamos los cambios en una nueva rama, autorizo que cambies codigo pero antes registra todo» (sesión del 2026-10-28). Autoriza T-019-01..15 en `feature/019-migracion-firebase`. No autoriza merge, despliegue ni creación de cuentas.

«1. autorizo a instalarlos con winget, 2. las privacidad sobre todo, y 3. deja pendiente el crear el proyecto firebase, el servicio en Render y la tarea en cron-job.org. puedes seguir con T-019-04 si lo demas esta listo» (2026-10-28). Autoriza instalar JDK 21, Node LTS y `firebase-tools` (D-099) y agrega T-019-16 (D-098).

## Registro de ejecución

| Fecha | Tarea | Resultado |
|---|---|---|
| 2026-10-28 | T-019-01 | Spec, plan y tareas; D-081..D-097 en DECISIONES; índice de specs; estado con los pendientes 22–25; sección de la rama en AGENTS y CLAUDE. Comprobado con metadatos de Git que `backend/.env` del base nunca se versionó (D-097). Sin código |
| 2026-10-28 | T-019-02 | `git archive` del commit `518792263c44`: 97 archivos versionados (sin `.env`, entornos ni compilados) en `backend/`, `firebase/`, `firebase.json`, `.firebaserc`, `portal/` (su `web/`), `docs/base-fastapi/` y `backend/scripts/dev-api.ps1`. `.gitignore` ampliado. `.venv-backend` con Python 3.12.4 y `requirements-dev.txt`. `python -m pytest`: **22 aprobadas, 186 omitidas** (integración sin emuladores, P-019-01) en 96 s |

## Reanudación

Última acción: T-019-02 cerrada. Siguiente: T-019-04 (nodos y contrato Edge), que puede avanzar con pruebas unitarias; T-019-03 espera P-019-01. Bloqueos: P-019-01 (Java y Node) para la integración; P-019-02 (diferencias 4 y 5) antes de T-019-06; P-019-03 antes de T-019-07.

## Aceptación del usuario

Pendiente.
