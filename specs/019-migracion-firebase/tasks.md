# Tareas — 019 / Migración a FastAPI + Firebase

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md).
Estado: T-019-01..06, 08, 09, 12 y 16 hechas (backend completo salvo el despliegue; app con alertas y privacidad); el resto, pendientes. Implementación autorizada: SÍ, T-019-01..15 (2026-10-28), sin merge, despliegue ni cuentas reales; cada una de esas acciones necesita autorización aparte.
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
- [x] T-019-03 — Herramientas y emuladores.
  - RF: RF-019-01.
  - Depende de: T-019-02 y D-099 (instalación de JDK 21, Node LTS y `firebase-tools` con `winget`, autorizada).
  - Archivos previstos: `docs/ENTORNO_Y_VERIFICACION.md`, `.venv-backend` (local, no versionado).
  - Hecho cuando: `firebase emulators:start` funciona y la suite completa del backend pasa sin omisiones.
- [x] T-019-04 — Nodos y contrato Edge.
  - RF: RF-019-02, RF-019-03, RF-019-05, RF-019-10, RF-019-11, RF-019-22.
  - Depende de: T-019-02 (T-019-03 para correr la integración).
  - Archivos previstos: `backend/app/api/edge.py`, `api/v1/nodes.py`, `services/nodes.py`, `services/observations.py`, `models/nodes.py`, `firebase/firestore.indexes.json`, pruebas.
  - Hecho cuando: cada caso de `EdgeView` y `PhoneObservationsView` tiene su prueba, más la caché invalidada al revocar y la prueba de presupuesto. `edge.test_*` pasan sin cambios.
- [x] T-019-05 — Alertas y push.
  - RF: RF-019-04, RF-019-05, RF-019-09.
  - Depende de: T-019-04.
  - Archivos previstos: `services/alerts.py`, `services/push.py`, `api/v1/alerts.py`, `api/v1/devices.py`, pruebas con FCM simulado.
  - Hecho cuando: una caída crea la alerta y solicita el push solo a los destinatarios con permiso y plan; los avisos de cámara salen una vez por episodio; el texto no contiene datos clínicos.
- [x] T-019-06 — Consentimiento, reloj y tick del cron.
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

- [x] T-019-08 — Base de la app dentro de `mobile/`.
  - RF: RF-019-12, RF-019-18.
  - Depende de: T-019-02.
  - Archivos previstos: `mobile/lib/**`, `mobile/test/**`, `mobile/pubspec.yaml`, `mobile/assets/branding`, `mobile/assets/fonts`.
  - Hecho cuando: la app del base compila con nuestro identificador, plugin y assets; las versiones de FlutterFire son compatibles entre sí; `flutter analyze` está limpio y `flutter test` pasa.
  - Cómo (2026-10-28, antes del código):
    - `lib/` y `test/` se reemplazan por los del commit `518792263c44`.
    - Se mantiene el paquete de Dart `vigia_mobile`, cambiando `package:vigia/` en los `import` del base. Así `android/`, `ios/`, `web/`, `tool/` y el identificador `cl.vigia.vigia_mobile` no cambian.
    - Se suman `assets/branding` y `assets/fonts` del base a `assets/guides` y `assets/models`.
    - Las dependencias del base se unen con las nuestras del plan (`camera`, `vigia_pose`, `flutter_local_notifications`, `timezone`, `firebase_messaging`, `url_launcher`, `google_sign_in`), con FlutterFire en una sola versión mayor de `firebase_core`. Salen `http` y `flutter_secure_storage`: solo los usaba la app anterior y vuelven si una tarea de portado los necesita.
    - Nuestras pantallas y pruebas salen de `lib/` y `test/` y se portan desde `develop` en T-019-09..12. Mientras tanto, la app de esta rama no tiene detección, reloj, avisos locales ni pantallas de privacidad.
- [x] T-019-09 — Cinco secciones y Alertas.
  - RF: RF-019-13, RF-019-14.
  - Depende de: T-019-08 y T-019-05.
  - Hecho cuando: hay pruebas de navegación y de la lista de alertas, y las 5 etiquetas caben a 360 dp.
  - Cómo (2026-10-28, antes del código):
    - `features/alerts` con la bandeja `GET /v1/me/alerts` y «Marcar como atendida» (`POST .../attend`; un 409 recarga la lista).
    - La lista se recarga al abrir, al volver la app al primer plano y al deslizar hacia abajo.
    - La sección Posturas queda como pantalla pendiente hasta T-019-10.
- [ ] T-019-10 — Posturas: teléfono, reloj y nodo.
  - RF: RF-019-15.
  - Depende de: T-019-08, T-019-04 y T-019-06.
  - Hecho cuando: las pruebas portadas de `clock_panel`, `camera_state` y `pose_classifier` pasan con los nuevos proveedores de datos.
- [ ] T-019-11 — Push y recordatorios locales de respaldo.
  - RF: RF-019-16, RF-019-19.
  - Depende de: T-019-08 y T-019-06.
  - Hecho cuando: las pruebas cubren el mismo identificador de toma, la cancelación al registrar y la recarga sin temporizador de 60 s.
- [x] T-019-12 — Política y consentimiento en la app.
  - RF: RF-019-17.
  - Depende de: T-019-08 y T-019-06.
  - Hecho cuando: las pruebas portadas de `privacy_test` y `login_consent_test` pasan.
  - Cómo (2026-10-28, antes del código):
    - **Política (D-101):** la sesión consulta `GET /v1/privacy` después de `/me`; con la política pendiente, la app muestra la política y la acepta dentro de ella.
    - **Consentimientos:** sección «Privacidad» en la ficha. El dueño registra el consentimiento de cuidado y el de detección (titular o representante con nombre y relación) y los revoca; las demás personas ven el estado.
    - **Exportar:** «Descargar mis datos» en Cuenta, y la exportación del paciente en su ficha, solo para el dueño (D-102).
    - **Eliminar:** el paciente se elimina escribiendo su nombre (dueño). La cuenta se elimina con la contraseña, que reautentica en Firebase para que el token tenga un `auth_time` reciente; el backend borra la cuenta de Firebase.
    - Origen: «puedes agregar alertas y privacidad?» (2026-10-28).

- [x] T-019-16 — Privacidad en el backend: purga, exportación y eliminación (D-098). Hecha la parte del backend; las pantallas siguen en T-019-12 y T-019-13.
  - RF: RF-019-24, RF-019-25, RF-019-26, RF-019-27.
  - Depende de: T-019-06 (tick y consentimiento).
  - Archivos previstos: `services/retention.py`, `services/export.py`, `services/erase.py`, `api/v1/privacy.py`, pruebas; pantallas de exportar y eliminar en la app (T-019-12) y en el portal (T-019-13).
  - Hecho cuando: hay pruebas de cada plazo (justo antes y después del límite), de que la exportación no lleva tokens, hashes ni códigos, del borrado completo del paciente, y del rechazo de la eliminación de cuenta sin inicio de sesión reciente, con autor anónimo en pacientes ajenos.

## Correcciones de la revisión QA del 2026-10-28

Origen: [QA_2026-10-28.md](../../docs/QA_2026-10-28.md). Autorización: «corrige el hallazgo alto y los de backend» (2026-10-28).

- [x] T-019-17 — Correcciones del backend: QA-02, QA-06, QA-07 y QA-08.
  - **QA-02:**
    - Las rutas del nodo y del teléfono leen el cuerpo por partes y cortan al pasar de 4 KB, con `Content-Length` revisado antes de leer.
    - Responden 400, igual que hoy: el nodo descarta el ítem y el contrato Edge no cambia.
    - El teléfono revisa el largo antes de parsear el JSON.
  - **QA-06:** sin `/docs`, `/redoc` ni `/openapi.json` en producción.
  - **QA-07:** si `VIGIA_ENVIRONMENT` no se declara, vale `production` sin emuladores y `development` con emuladores. Así, olvidar la variable en Render no desactiva protecciones.
  - **QA-08:** en producción, `VIGIA_CRON_SECRET` va vacío (tick desactivado) o tiene 32 caracteres o más.
  - **QA-09 queda fuera:** cambiar `Message.token` por `fid` también cambia lo que registra la app; se evalúa en T-019-11.
  - Hecho cuando: hay una prueba por corrección (incluido un cuerpo de 5 MB sin token) y la suite completa pasa.
- [ ] T-019-18 — Verificación de correo en la app (QA-01).
  - Al crear la cuenta, la app envía el correo de verificación.
  - Si unirse responde `email_not_verified`, la app muestra «Verifica tu correo», con «Reenviar correo» y «Ya lo verifiqué». Este último recarga la cuenta, renueva el token y reintenta.
  - La regla sigue en el backend: solo producción la exige, así que el flujo local no cambia.
  - Hecho cuando: hay pruebas del envío al crear la cuenta, del aviso, del reenvío y del reintento con el token renovado.

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

«detenlo y autorizo T-019-08» (2026-10-28, después del recorrido en vivo). Confirma T-019-08.

«no por ahora deten el servidor y haz commit y push para que puedan acceder los otros miembros del equipo» (2026-10-28). Autoriza subir `feature/019-migracion-firebase` a `origin` para el equipo. No autoriza merge, PR ni despliegue. La prueba en vivo del detector de caídas con la cámara del PC queda para más adelante.

## Registro de ejecución

| Fecha | Tarea | Resultado |
|---|---|---|
| 2026-10-28 | T-019-01 | Spec, plan y tareas; D-081..D-097 en DECISIONES; índice de specs; estado con los pendientes 22–25; sección de la rama en AGENTS y CLAUDE. Comprobado con metadatos de Git que `backend/.env` del base nunca se versionó (D-097). Sin código |
| 2026-10-28 | T-019-02 | `git archive` del commit `518792263c44`: 97 archivos versionados (sin `.env`, entornos ni compilados) en `backend/`, `firebase/`, `firebase.json`, `.firebaserc`, `portal/` (su `web/`), `docs/base-fastapi/` y `backend/scripts/dev-api.ps1`. `.gitignore` ampliado. `.venv-backend` con Python 3.12.4 y `requirements-dev.txt`. `python -m pytest`: **22 aprobadas, 186 omitidas** (integración sin emuladores, P-019-01) en 96 s |
| 2026-10-28 | T-019-03 | `winget`: Temurin JDK 21.0.12.1 y Node.js 24.22.1; `npm i -g firebase-tools` 15.34.1. Emuladores Auth y Firestore (`demo-vigia-test`) listos. Backend: **208 aprobadas, 0 omitidas** en 52 s. Reglas de Firestore (`firebase/`, vitest): **7/7**. Comandos en `docs/ENTORNO_Y_VERIFICACION.md` |
| 2026-10-28 | T-019-04 | `models/nodes.py`, `services/nodes.py`, `services/edge_cache.py` (D-095), `services/consent.py` (consulta, falla cerrado), `api/v1/nodes.py`, `api/edge.py` en `/api/v1/edge`; la caché se vacía al revocar, cambiar el plan, editar planes (admin) y archivar. Backend **263 OK** (55 nuevas), 4/4 mutaciones detectadas, Edge 56 OK sin cambios y prueba de punta a punta con `edge.run.Uplink` real (caída entregada). Diferencias 8 y 9 en el plan. [Validación](validation.md) |
| 2026-10-28 | T-019-05 | `services/alerts.py`, `services/push.py`, `services/devices.py`, `models/alerts.py`, `api/v1/alerts.py`; `VIGIA_PUSH_ENABLED` en la configuración; la caída y su alerta en el mismo lote con push después de responder al nodo; inmovilidad, cámara ciega y nodo sin señal por `alerts.run_cycle()` (lo llamará el tick, T-019-06); índice de grupo `alerts.pushPending`. Backend **282 OK** (19 nuevas con FCM simulado), 6/6 mutaciones detectadas |
| 2026-10-28 | T-019-06 | Política de la cuenta (`get_registered_user` / `get_current_user`, `/v1/privacy`), consentimiento por finalidad con historial (`/v1/patients/{id}/consents`), consentimiento de cuidado exigido en las 9 escrituras de `care.py` y `medications.py`; reloj (`/timer`, `/me/timer-schedule`) reiniciado por ambos registros de posición; recordatorios de tomas y del reloj (`services/reminders.py`, cada 5 min como máximo) y `POST /internal/tick` con `X-Cron-Secret`; opciones `VIGIA_PRIVACY_ENFORCED`, `VIGIA_PRIVACY_POLICY_VERSION` y `VIGIA_CRON_SECRET`; índice de grupo `medications.active`. Backend **316 OK** (34 nuevas), 9/10 mutaciones detectadas (la décima es equivalente). Diferencias 10 y 11 en el plan |

| 2026-10-28 | T-019-16 | `services/erase.py` (paciente con confirmación de nombre; cuenta con inicio de sesión de hace 5 minutos o menos, pacientes propios borrados (D-065), autor anónimo en pacientes ajenos y borrado en Firebase Auth), `services/export.py` (cuenta y paciente, sin tokens, hashes ni códigos), `services/retention.py` (plazos de D-064, una vez al día desde el tick), rutas en `api/v1/privacy.py`; `archivedAt` al archivar; estado de cuenta `deleted`; `auth_time` en la identidad; índices de grupo `observations.observedAt` y `alerts.occurredAt`. Backend **327 OK** (11 nuevas), 11/11 mutaciones detectadas |
| 2026-10-28 | T-019-08 | `lib/` (50 archivos) y `test/` (14) desde `518792263c44` con `git archive`; `package:vigia/` → `package:vigia_mobile/`; `assets/branding` y `assets/fonts` (Nunito, OFL) junto a `guides` y `models`; `pubspec.yaml` con Riverpod, go_router, dio, `firebase_core` ^5.1.0, `firebase_auth` ^7.0.1 y `firebase_messaging` ^17.0.1 (resuelto por `flutter pub add`), más `camera`, `vigia_pose`, avisos locales, `timezone`, `url_launcher`, `google_sign_in` y `mocktail`; sin `http` ni `flutter_secure_storage`. `flutter analyze` limpio, `flutter test` **67/67**, `flutter build apk --debug` OK con `VigiaPosePlugin` registrado y los assets dentro. Nuestras pantallas se portan en T-019-09..12 |
| 2026-10-28 | T-019-09 y T-019-12 | Un solo commit, porque ambas tocan el router. `features/alerts` (bandeja, atender, recarga al volver al primer plano) y la barra de 5 secciones con Posturas pendiente (T-019-10). `features/privacy`: política aceptada en la app (D-101, estado de sesión `NeedsPolicy`), consentimientos por finalidad en la ficha, con aviso si falta el de cuidado, descarga JSON con «Copiar» (D-102), eliminación del paciente con su nombre y de la cuenta con la contraseña (reautenticación en Firebase). Las pruebas encontraron un error: una finalidad nunca registrada se mostraba como «Revocado»; ahora se usa `revokedAt`. Flutter **92 OK** (25 nuevas: 9 de alertas y 16 de privacidad) y 7/7 mutaciones detectadas |
| 2026-10-28 | T-019-17 | `core/body.py` (`read_limited`: `Content-Length` y lectura por partes con tope de 4 KB) en las rutas del nodo y del teléfono; el teléfono revisa el largo antes de parsear; `environment` sin declarar = `production` sin emuladores; secreto del cron de 32 caracteres o más en producción; sin `/docs`, `/redoc` ni `/openapi.json` en producción; `.env.example` actualizado. Backend **337 OK** (10 nuevas) y 7/7 mutaciones detectadas |

## Reanudación

Última acción: T-019-09 y T-019-12 cerradas (alertas y privacidad en la app). Siguiente: T-019-10 (Posturas: teléfono, reloj y nodo) y T-019-11 (push y avisos locales), o T-019-07 si el proyecto Firebase ya existe (D-100). Correcciones de la QA del 2026-10-28: T-019-17 (backend) hecha; T-019-18 (verificación de correo en la app) en curso. Pendiente del propietario: P-019-04 (reloj solo en Plus y Premium), registrado el 2026-10-28 a su pedido. Para probar, primero levantar los emuladores (ver `docs/ENTORNO_Y_VERIFICACION.md`). Bloqueos: P-019-01 (Java y Node) para la integración; P-019-02 (diferencias 4 y 5) antes de T-019-06; P-019-03 antes de T-019-07.

## Aceptación del usuario

Pendiente.
