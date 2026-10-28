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
- Consentimiento por API, reloj y tick (T-019-06); privacidad (T-019-16).
- Nodo con cámara real contra este backend y push en Android: punto de control (T-019-07), que necesita el proyecto Firebase (D-100).
- La demora de 0,029 s es la recepción en una red local con emuladores; no mide la alerta de caída en ≤ 10 s.
