# Validación — 019 / Migración a FastAPI + Firebase

Spec: [spec.md](spec.md). Tareas: [tasks.md](tasks.md).
Entorno: Windows 10, Python 3.12.4 (`.venv-backend`), Temurin JDK 21.0.12.1, Node.js 24.22.1, firebase-tools 15.34.1, emuladores de Auth y Firestore con el proyecto `demo-vigia-test`.

Solo se registra lo ejecutado. Ningún RNF del informe se declara cumplido aquí.

## Resultados por tarea

| Fecha | Tarea | Comando | Resultado |
|---|---|---|---|
| 2026-10-28 | T-019-02 | `python -m pytest` (desde `backend/`, sin emuladores) | 22 aprobadas, 186 omitidas |
| 2026-10-28 | T-019-03 | `python -m pytest` con emuladores | 208 aprobadas, 0 omitidas (52 s) |
| 2026-10-28 | T-019-03 | `npm test` en `firebase/` con emuladores | 7/7 |
| 2026-10-28 | T-019-04 | `python -m pytest` con emuladores | **263 aprobadas**: las 208 del base más 52 en `test_nodes.py` y 3 en `test_edge_budget.py` (47 s) |
| 2026-10-28 | T-019-04 | Mutaciones temporales en `services/nodes.py` | 4/4 detectadas: revocar sin vaciar la caché, aceptar claves extra, inmovilidad con postura indeterminada y escribir la última señal en cada renovación |
| 2026-10-28 | T-019-04 | `python -m unittest edge.test_posture edge.test_fall edge.test_run` (`.venv-edge-win`) | 56 OK; `edge/` sin cambios |
| 2026-10-28 | T-019-04 | Prueba de punta a punta: backend local (uvicorn, puerto 8765) con emuladores; `backend/scripts/smoke_edge_setup.py` crea dueña, paciente Premium con consentimiento y nodo; `backend/scripts/smoke_edge_uplink.py` usa `edge.run.Uplink` **sin cambios** | Permiso de captura obtenido; caída entregada (`pendientes=0`); el backend la guardó con `receivedAt − observedAt` = 0,029 s; `GET /camera` = `persona_no_visible`; la observación aparece en `GET /observations` con `source = "Dormitorio"` |

| 2026-10-28 | T-019-05 | `python -m pytest` con emuladores | **282 aprobadas** (19 nuevas en `test_alerts.py`, con FCM simulado en `push.transport`) |
| 2026-10-28 | T-019-05 | Mutaciones temporales en `alerts.py` y `push.py` | 6/6 detectadas: destinatarios sin `alerts.handle`, todo con prioridad alta, sin recibo (push duplicado), una falla de FCM que no queda pendiente, anunciar episodios de más de 1 hora e ignorar `advancedAlerts` del plan |

| 2026-10-28 | T-019-06 | `python -m pytest` con emuladores | **316 aprobadas** (34 nuevas en `test_privacy.py`, `test_timer.py` y `test_tick.py`) |
| 2026-10-28 | T-019-06 | Mutaciones temporales | 9/10 detectadas: no exigir la política; no exigir el consentimiento de cuidado; revocar detección sin vaciar la caché; un cambio de posición que crea el reloj; un cambio tardío que lo retrocede; sin control de `generation`; la familia recibe recordatorios; recordar tomas ya registradas; ignorar los avisos locales del reloj. La décima (quitar `not secret` en el tick) es equivalente: con el secreto vacío la comparación igual falla con 401 |

| 2026-10-28 | T-019-16 | `python -m pytest` con emuladores | **327 aprobadas** (11 nuevas en `test_privacy_rights.py`) |
| 2026-10-28 | T-019-16 | Mutaciones temporales en `export.py`, `erase.py` y `retention.py` | 11/11 detectadas: exportar el token y el hash del nodo; exportar la huella del código de invitación; omitir los registros en pacientes ajenos; borrar sin confirmar el nombre; dejar nodos, invitaciones y membresías; nodo autorizado tras borrar el paciente; borrar la cuenta sin inicio de sesión reciente; no borrar la cuenta de Firebase; borrar riesgos antes de 1 año; purgar archivados recientes; purgar en cada tick |
| 2026-10-28 | Recorrido en vivo | Backend con uvicorn en `:8000` con la privacidad exigida y los emuladores. Cuentas creadas e iniciadas por REST en el emulador de Auth, como la app. El plan Premium se asignó por SDK, porque el pago del portal es T-019-13 | **52/52**: registro; política y consentimientos exigidos; HU-01 medicamento y tarea; invitaciones de cuidadora y familiar; HU-02 agenda; HU-03 toma, con repetida = 409; HU-04 reloj y cambio de posición, con generación vieja = 409; teléfonos; HU-05 caída del Edge → alerta visible y atendida por la familia; tick con y sin secreto; HU-06 historial; exportar; borrar cuenta y paciente; nodo rechazado después |
| 2026-10-28 | Portal | `npm ci`, `npm test`, `npm run build`, `npm run lint` en `portal/`; `npm run dev` en `:5173` | 2/2 pruebas, compilación y lint OK. Portal servido. CORS: la API acepta `localhost:5173` y `127.0.0.1:5173` y rechaza un origen ajeno. El portal solo muestra la salud de la API; HU-07 es T-019-13 |
| 2026-10-28 | App actual | `flutter analyze`, `flutter test` en `mobile/` | Sin problemas; 51/51. La app sigue hablando con la API de Django (`/api/v1/agenda`, `access/accept`…): contra el backend nuevo no funciona hasta T-019-08 |
| 2026-10-28 | T-019-08 | `flutter analyze`, `flutter test`, `flutter build apk --debug --target-platform android-arm64` en `mobile/` | Sin problemas; **67/67** (pruebas del base); APK compilado en 95 s con `cl.vigia.vigia_mobile`, `VigiaPosePlugin` registrado y los assets de marca, fuentes, guías y modelo. Aviso de Gradle: `firebase_auth` y `firebase_core` aplican el plugin de Kotlin que Flutter dejará de aceptar; se revisa al actualizar FlutterFire. Sin probar en un teléfono |
| 2026-10-28 | App en Android físico | ELI NX9 (Android 16) por USB con `adb reverse`; backend local con emuladores (`demo-vigia`) y `VIGIA_PRIVACY_ENFORCED=false`, porque la app base aún no tiene la pantalla de política (T-019-12); interfaz manejada con `adb` (toques, texto y capturas) | Funcionó en el teléfono:<br>• Crear cuenta en el emulador de Auth y completar el perfil (`/v1/auth/register` 201).<br>• **HU-01:** paciente, medicamento a las 08:00 y tarea (201).<br>• **HU-07 en la app:** cambio simulado de Gratis a Premium (`/v1/me/subscription/change` 200).<br>• Invitar a la cuidadora y unirse con el código (`/v1/invitations/accept` 200); la cuidadora no ve "Editar" ni puede agregar medicamentos.<br>• **HU-02:** agenda del día.<br>• **HU-03:** toma "dada con retraso" con motivo.<br>• Tarea realizada.<br>• **HU-04:** cambio de posición (Premium); "3 de 3 registrados".<br>• **HU-06:** historial con autor (Tú / Rosa Duena) y filtros.<br>• **HU-05 (backend):** una caída enviada con el contrato del Edge creó la alerta.<br>No disponible todavía:<br>• La pestaña Alertas es un marcador (T-019-09).<br>• No hubo push (FCM sin proyecto real; la app no registra el teléfono, T-019-11). |
| 2026-10-28 | T-019-09 y T-019-12 | `flutter analyze`, `flutter test` | Sin problemas; **92/92** (9 nuevas en `alerts_test.dart` y 16 en `privacy_test.dart`, portadas de `privacy_test` y `login_consent_test` de `develop`). Mutaciones 7/7 detectadas: política pendiente ignorada; representante sin nombre ni relación; borrar el paciente sin el nombre; eliminar la cuenta sin reautenticar; nunca registrado mostrado como revocado; atender sin recargar; Posturas con una etiqueta que no cabe en 360 dp |

Plazos de D-064 en este backend: los intentos de código (24 h) no aplican, porque el backend base no los guarda. Las alertas se conservan 1 año, como las observaciones con riesgo. El borrado no es transaccional (Firestore no borra cientos de documentos en una transacción): avanza por partes y se puede repetir hasta terminar.

Lo que comprueban las pruebas de T-019-05:
- **Caída:** la alerta (`obs_<observación>`) se crea con la observación; el push sale una vez a dueña, familiar y cuidadora, y no a la miembro sin `alerts.handle`, con texto genérico, prioridad alta y visibilidad privada.
- **Reintentos:** un reintento del nodo no duplica la alerta ni el push.
- **Inmovilidad:** sale en el ciclo, con prioridad normal.
- **Sin envío:** sin `advancedAlerts` la alerta se guarda sin push. Una cuenta suspendida no recibe nada.
- **Fallas de FCM:** el dispositivo que falló se reintenta en el ciclo sin repetir a los demás; un token no registrado desactiva el dispositivo. Con el push apagado, la alerta espera hasta 1 hora.
- **Cámara:** nodo sin señal y cámara ciega crean una alerta por episodio; con poca luz, nunca se conectó, episodio antiguo, sin consentimiento o sin cámara en el plan, ninguna.
- **Consulta:** lista ordenada, atención única (409 la segunda), `/v1/me/alerts` con los nombres de los pacientes y las reglas de instalación de los dispositivos.

`firebase_admin` 7.7.0 marca `Message.token` como obsoleto y propone `fid` (identificador de instalación de Firebase). Se mantiene el token FCM, que sigue funcionando; el cambio se evalúa con la app (T-019-11).

## Cuota de Firestore (RF-019-11)

`test_edge_budget.py` simula un día (8.640 renovaciones cada 10 s) con un reloj falso: como máximo 1.441 cargas de autorización (~7.200 lecturas) y 2.881 escrituras de la última señal, frente a ~43.000 lecturas y 8.640 escrituras sin caché. Es un conteo de llamadas del backend, no una medición en un proyecto Firebase real.

## No comprobado

- Push real: FCM está simulado; la entrega en un teléfono requiere el proyecto Firebase (D-100).
- El tick con un cron real (cron-job.org) y Render (D-100); los recordatorios en un teléfono.
- Las pantallas de exportar y eliminar en la app y el portal (T-019-12, T-019-13). La revisión legal de la política sigue pendiente (D-067).
- Nodo con cámara real contra este backend y push en Android: punto de control (T-019-07), que necesita el proyecto Firebase (D-100).
- La demora de 0,029 s es la recepción en una red local con emuladores; no mide la alerta de caída en ≤ 10 s.
