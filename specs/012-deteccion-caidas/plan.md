# Plan técnico — 012 / Detección de caídas

Spec: [spec.md](spec.md). Estado: aprobado para implementar por el usuario el 2026-10-22 (mismo mensaje).

## Inspección de la base

Leídos: `edge/posture.py` (clasificador calibrado e `ImmobilityRule`), `edge/run.py` (bucle MediaPipe VIDEO, arrendamiento `edge/status`, envío a `edge/observations`), `edge/test_posture.py`, `edge/README.md`; `web/CuidadosApp/api/detection.py` (`EdgeView`, `ObservationsView`), `mobile_models.py` (`PostureObservation.risk`, `received_at`), `management/commands/send_mobile_reminders.py` (vía de avisos), `test_mobile.py`; `mobile/lib/features/patients/patient_screen.dart` (texto del historial). Git limpio al iniciar (`0dcaee2`).

Hallazgo clave: `run.py` usa `pose_world_landmarks`, cuyo origen es el centro de las caderas; con ellos la altura de la cadera es siempre ≈ 0 y no sirve para medir descenso. La regla de caída usa `pose_landmarks` (normalizados de imagen) del mismo resultado.

## Diseño propuesto

- `edge/fall.py` (nuevo, Python puro, sin dependencias): `FallConfig` (dataclass con defectos, validación y carga JSON), `frame_features()` (cadera, tronco, ángulo, rectángulo) y `FallDetector` (máquina de estados `idle → confirming → alerted`). Separado de `posture.py` porque usa otras coordenadas y otro ciclo de vida.
- `edge/metrics.py` (nuevo): `LatencyStats` (promedio, p95 por rango más cercano, máximo) para `run.py` y `bench.py`.
- `edge/run.py`: extrae también landmarks de imagen, alimenta `FallDetector`, registra inferencia por cuadro, envía la caída con reintento y pasa de `print` a `logging` (con `--log-file` opcional). Los argumentos `--fall-*` se generan desde `FallConfig`.
- `edge/bench.py` (nuevo): procesa videos con marca de tiempo del video, sin servidor ni credencial.
- Backend: `risk="fall"` en `choices`, validación en `EdgeView`, log de recepción, `received_at` en `ObservationsView`, caídas en `send_mobile_reminders` con texto y prioridad propios.
- Móvil: texto «Posible caída» en el historial.

## Mapa por requisito

| RF | Archivos | Cambio | Evidencia |
|---|---|---|---|
| RF-012-01..04, 10 | `edge/fall.py` (nuevo), `edge/test_fall.py` (nuevo) | Regla, config y secuencias sintéticas | `python -m unittest edge.test_fall` |
| RF-012-05, 08 | `edge/run.py`, `edge/metrics.py` (nuevo) | Integración, reintento, logging | `edge.test_fall` (métricas), revisión de código; ejecución real pendiente de cámara |
| RF-012-09 | `edge/bench.py` (nuevo) | Benchmark de video | `--help`; ejecución con video autorizado pendiente |
| RF-012-06 | `mobile_models.py`, migración `0007`, `api/detection.py` | Riesgo `fall`, log, `received_at` | `CuidadosApp.test_mobile` |
| RF-012-07 | `send_mobile_reminders.py` | Caídas en la vía de avisos | Test con Firebase simulado |
| RF-012-06 (UI) | `patient_screen.dart` | Texto de caída | `flutter analyze` |

## Datos y contratos

Contrato del nodo sin campos nuevos; `risk ∈ {"", "immobility", "fall"}`. `immobility` exige postura distinta de `indeterminada`; `fall` no (la persona en el suelo no coincide con las referencias calibradas en cama). Deduplicación por `event_id` y ventana de `observed_at` (−2 min / +30 s) se mantienen: el nodo deja de reintentar a los 110 s.

## Migraciones y reversión

`0007_alter_postureobservation_risk`: `AlterField` de `choices` (sin cambio SQL de columna). Reversión: migrar a `0006`; las filas `fall` quedan como texto válido de 24 caracteres. No se ejecuta migración real.

## Plan de pruebas

Edge: caída (una emisión, latencia ≈ `confirm_seconds`), caída con recuperación, caída con pérdida de señal, persistencia sin repetición, sentarse rápido, sentadilla, inclinarse, acostarse lento y rápido en cama, sin señal, configuración (JSON, rangos, claves), métricas. Backend: aceptación `fall` con `indeterminada`, rechazos, historial con `received_at`, push simulado sin duplicar y con texto de caída. Regresión: suites Django y `edge.test_posture`.

## Riesgos, alternativas y dependencias

- Alternativa descartada: clasificador entrenado (sin datos etiquetados, no determinista).
- Riesgo: la vista de frente reduce la relación de aspecto; mitigable bajando `aspect_ratio`/`aspect_change` tras el protocolo.
- Riesgo: pérdida de detección de la persona en el suelo; `max_gap_seconds` la tolera hasta 2 s.
- Sin paquetes nuevos.

## Documentos afectados

`edge/README.md` (regla, parámetros, métricas, bench, protocolo de 20 caídas), `specs/README.md`, `docs/ESTADO_PROYECTO.md`, `docs/TRAZABILIDAD.md`, `docs/DECISIONES.md`, `validation.md`.

## Decisiones para implementar

Ninguna bloqueante. P-012-01 y P-012-02 quedan abiertas (ver spec).
