# Tareas — 012 / Detección de caídas

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md).
Estado: implementadas; verificación sintética OK, prueba en vivo y protocolo pendientes. Implementación autorizada: SÍ (usuario, 2026-10-22, mismo mensaje que pidió la spec).

- [x] T-012-01 — Regla de caída y configuración en `edge/fall.py`.
  - RF: RF-012-01..04.
  - Depende de: ninguna.
  - Archivos: `edge/fall.py`.
  - Hecho cuando: `FallDetector` y `FallConfig` con defectos documentados y validación.
- [x] T-012-02 — Pruebas sintéticas de caída y actividades cotidianas.
  - RF: RF-012-01..04, RF-012-10.
  - Depende de: T-012-01.
  - Archivos: `edge/test_fall.py`.
  - Hecho cuando: `python -m unittest edge.test_fall` pasa; sentarse/agacharse/acostarse sin alerta.
- [x] T-012-03 — Métricas de inferencia y logging del nodo.
  - RF: RF-012-08.
  - Depende de: ninguna.
  - Archivos: `edge/metrics.py`, `edge/run.py`.
  - Hecho cuando: promedio/p95 probados; `run.py` los registra por intervalo junto a impacto y confirmación.
- [~] T-012-04 — Integración y envío de la caída con reintento.
  - RF: RF-012-05.
  - Depende de: T-012-01, T-012-03.
  - Archivos: `edge/run.py`.
  - Hecho cuando: `--fall-*`/`--fall-config` disponibles; caída se envía con `risk="fall"`, mismo `event_id` en reintentos.
- [x] T-012-05 — Script `edge/bench.py`.
  - RF: RF-012-09.
  - Depende de: T-012-01, T-012-03.
  - Hecho cuando: `--help` funciona y reporta latencia, FPS y conteo por video.
- [x] T-012-06 — Backend: riesgo `fall`, migración aditiva, log de recepción, historial.
  - RF: RF-012-06, RF-012-08.
  - Archivos: `mobile_models.py`, `migrations/0007_*`, `api/detection.py`.
  - Hecho cuando: tests de aceptación/rechazo pasan; `makemigrations --check` limpio.
- [x] T-012-07 — Aviso push de caída.
  - RF: RF-012-07.
  - Archivos: `management/commands/send_mobile_reminders.py`, `test_mobile.py`.
  - Hecho cuando: test con Firebase simulado envía un push de caída y no duplica.
- [x] T-012-08 — Texto de caída en la app móvil.
  - RF: RF-012-06.
  - Archivos: `mobile/lib/features/patients/patient_screen.dart`.
  - Hecho cuando: `flutter analyze` sin errores nuevos.
- [~] T-012-09 — Documentar regla, bench y protocolo de 20 caídas; validar y cerrar.
  - RF: todos.
  - Archivos: `edge/README.md`, `validation.md`, índices y estado.
  - Hecho cuando: resultados reales en validation.md y documentos actualizados.

- [x] T-012-10 — Envío desacoplado del bucle de cuadros (QA-2026-10-22-01).
  - RF: RF-012-11, RF-012-12.
  - Depende de: T-012-04.
  - Archivos: `edge/run.py` (`Uplink` con hilo, cola, backoff y lease; `Monitor` sin red), `web/CuidadosApp/api/detection.py` (riesgos hasta 1 h).
  - Hecho cuando: una demora de 2,5 s o 5 s no impide confirmar la caída; red caída y recuperada entrega con `observed_at` original.
- [x] T-012-11 — Avisos push sin ventana de 2 minutos (QA-2026-10-22-02).
  - RF: RF-012-07.
  - Archivos: `send_mobile_reminders.py`, `test_mobile.py`.
  - Hecho cuando: un riesgo recibido tarde o con fallo de FCM se avisa una vez en una ejecución posterior.
- [x] T-012-12 — `main()` en funciones testeables y tests de entrega (QA-2026-10-22-03).
  - RF: RF-012-05, RF-012-11, RF-012-12.
  - Archivos: `edge/run.py`, `edge/test_run.py`.
  - Hecho cuando: tests de red lenta (2,5 y 5 s), caída y recuperación, reintento sin duplicado, expiración y denegación pasan.

## Autorización posterior

Usuario, 2026-10-22: «Te autorizo crear specs/012-deteccion-caidas/ (spec, plan, tasks) e implementarla completa en la misma sesión.» No autoriza producción, migración real ni cámara personal.

Usuario, 2026-10-22 (posterior): «Corrige QA-01, QA-02 y QA-03 antes de commitear la spec 012 […] haz los commits […] en la rama feature/deteccion-caidas y haz push.»

## Ejecución

| Fecha | Tarea | Archivos / comando | Resultado / pendiente |
|---|---|---|---|
| 2026-10-22 | T-012-01/02 | `edge/fall.py`, `edge/test_fall.py` | 11 tests OK; actividades cotidianas sin alerta |
| 2026-10-22 | T-012-03 | `edge/metrics.py`, `edge/run.py` | p95 probado; log en vivo pendiente |
| 2026-10-22 | T-012-04 | `edge/run.py` | Implementado (envío y reintento); **no ejecutado en vivo**: falta cámara autorizada y nodo de prueba |
| 2026-10-22 | T-012-05 | `edge/bench.py` | Ejecutado en Windows con video sintético sin personas |
| 2026-10-22 | T-012-06/07 | modelo, `0007`, `detection.py`, `send_mobile_reminders.py`, `test_mobile.py` | Django 178 OK |
| 2026-10-22 | T-012-08 | `patient_screen.dart` | analyze sin problemas, 19 OK |
| 2026-10-22 | T-012-09 | `edge/README.md`, validation, índices | Documentado; **protocolo de 20 caídas no ejecutado** |
| 2026-10-22 | T-012-10/12 | `edge/run.py`, `edge/test_run.py`, `detection.py` | Edge 22 OK (6 nuevos); mutación «envío en el bucle» detectada |
| 2026-10-22 | T-012-11 | `send_mobile_reminders.py`, `test_mobile.py` | Django 181 OK (3 nuevos) |

## Reanudación

Código y documentos completos. Siguiente: ejecutar `edge.run` contra un servidor de prueba con un nodo vinculado (T-012-04) y el protocolo de 20 caídas de `edge/README.md` (T-012-09, P-012-02); decidir la frecuencia de avisos (P-012-01). `[~]` = implementada, con verificación en vivo pendiente.

## Aceptación del usuario

Pendiente.
