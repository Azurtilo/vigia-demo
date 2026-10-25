# Validación — 012 / Detección de caídas

Fecha: 2026-10-22. Entorno: Windows 10, Python 3.12.4. Web con `.venv` raíz y `core.test_settings` (SQLite en memoria). Edge con `.venv-edge-win` recién creado desde `edge/requirements.txt` (MediaPipe 0.10.35, OpenCV 5.0.0.93) y modelo copiado de `mobile/assets/models/` a `edge/models/` (ignorada por Git). Flutter 3.47.7.
Referencia de código: sobre `0dcaee2`, cambios sin commit.
Estado: verificación técnica **sintética**. Sin personas reales, cámara, servidor en vivo ni Firebase real.

| RF | Prueba / comando | Esperado | Obtenido | Estado |
|---|---|---|---|---|
| RF-012-01/02 | `edge.test_fall`: `test_fall_is_emitted_once_after_confirmation`, `test_widescreen_coordinates_are_scaled` | 1 caída ≈ 5 s tras el impacto; 16:9 igual | OK | Verificado (sintético) |
| RF-012-02 | `test_getting_up_cancels`, `test_short_occlusion_is_tolerated_long_gap_cancels`, `test_no_signal_never_alerts`, `test_floor_calibration_blocks_falls_above_it` | Cancela al incorporarse, al perder la señal más de 2 s o si la cadera queda sobre `floor_hip_y`; tolera 1 s de oclusión | OK | Verificado (sintético) |
| RF-012-03 | `test_fall_stays_single_while_lying_long` (30 s en el suelo) | 1 caída | OK | Verificado (sintético) |
| RF-012-01 | `test_each_impact_condition_is_required` (subir cada umbral por separado) | Ninguna caída con cualquier condición incumplida | OK | Verificado (sintético) |
| RF-012-10 | `test_daily_activities_do_not_alert`: sentarse rápido, sentadilla, inclinarse, acostarse en la cama lento y dejarse caer en ella | Sin caída | OK | Verificado (sintético) |
| RF-012-04 | `test_config_file_arguments_and_validation`; `edge.bench --fall-recover-angle 70` | JSON + CLI con prioridad CLI; rechazo de claves o rangos inválidos | OK; el bench termina con «Configuración de caídas inválida» | Verificado |
| RF-012-05 | Revisión de `edge/run.py` | `risk="fall"`, reintento con mismo `event_id` ≤ 110 s | Implementado; **no ejecutado** con cámara ni servidor | Pendiente |
| RF-012-06 | `CuidadosApp.test_mobile.test_edge_fall_is_stored_in_history_with_reception_time` | 201 con `indeterminada`; 400 para `immobility`+`indeterminada`, riesgo desconocido o campo extra; historial con `received_at`; log de recepción | OK | Verificado |
| RF-012-07 | `test_fall_push_uses_existing_channel_once_and_first` (Firebase simulado en `sys.modules`) | Caída primero, texto propio, prioridad alta; inmovilidad sin prioridad; segunda ejecución sin duplicados | OK | Verificado (simulado); entrega FCM real pendiente |
| RF-012-08 | `MetricsTests.test_mean_p95_and_max`; revisión del log de `run.py` | Promedio 50,5, p95 95, máx 100 para 1..100 | OK; log en vivo no ejecutado | Parcial |
| RF-012-09 | `edge.bench` con video sintético de ruido (300 cuadros, 640×480, 30 FPS), en el scratchpad de la sesión | El script procesa y reporta | 0 personas, inferencia 12,73 ms promedio, 14,87 ms p95, 21,39 ms máx, 70,25 FPS, 0 caídas; `--json` OK | Script verificado; **la cifra no mide el KPI** (sin persona en el cuadro) |
| RF-012-11 | `edge.test_run.SlowNetworkTests` (servidor que retiene la respuesta 2,5 s y 5 s reales) | Caída confirmada y encolada antes de la respuesta; cada cuadro < 0,5 s; entregada una vez | OK. Mutación: enviar dentro del bucle → el test falla | Verificado (simulado) |
| RF-012-12 | `OutageTests` (red caída 6 intentos: backoff 1, 2, 4, 8, 16, 30 s; lease vencido; recuperación), `RetryTests` (respuesta perdida dos veces), expiración por tipo, 403 y 400 | Entrega con `observed_at`/`event_id` originales; 3 POST idénticos, 1 fila; ordinaria expira a 110 s, riesgo a 55 min | OK | Verificado (simulado) |
| RF-012-07 (corrección) | `test_late_or_failed_risk_push_is_retried_until_delivered_once`, `test_risk_older_than_push_window_is_not_announced`, `test_late_risk_is_accepted_but_ordinary_observations_expire` | Caída de hace 30 min y FCM fallando 2 veces → 1 push de caída y 1 de inmovilidad; riesgo de hace 2 h sin push; riesgo de 50 min aceptado, de 61 min y ordinaria de 5 min rechazados | OK | Verificado (Firebase simulado) |
| RF-012-06 (UI) | `flutter analyze`; `flutter test` | Sin problemas | Sin problemas; 19 OK | Verificado; visual en dispositivo pendiente |

Márgenes de las secuencias sintéticas (máximo por escenario; umbrales: ángulo 60°, aspecto 1,0, velocidad 1,5 troncos/s, descenso 0,8 troncos):

| Escenario | Ángulo | Aspecto | Velocidad | Descenso | Condiciones que fallan |
|---|---|---|---|---|---|
| Caída lateral | 85 | 12,4 | 2,65 | 1,59 | ninguna |
| Sentarse rápido | 15 | 0,49 | 1,36 | 0,82 | ángulo, aspecto, velocidad |
| Sentadilla | 40 | 0,70 | 1,59 | 1,27 | ángulo, aspecto |
| Inclinarse a recoger | 85 | 0,84 | 0,09 | 0,09 | aspecto, velocidad, descenso |
| Acostarse en la cama (lento o rápido) | 90 | alto | 0,45 | 0,45 | velocidad, descenso |

Las siluetas sintéticas son delgadas: el aumento de aspecto (`aspect_change`) discrimina poco en estas secuencias. Su efecto real se mide con el protocolo.

## Regresión de la base

Tras las correcciones QA (2026-10-22, posterior): Django `check` y `makemigrations --check` sin cambios, **181 OK**; Edge `edge.test_posture edge.test_fall edge.test_run` **22 OK** (7,9 s); Flutter analyze sin problemas, **19 OK**; ruff sin hallazgos en `edge/run.py` y `edge/test_run.py`.

Antes de las correcciones:

- Django: `check` sin problemas; `makemigrations --check --dry-run` sin cambios; `manage.py test UsuarioApp homeApp PlanesApp CuidadosApp --settings=core.test_settings` → **178 OK** (176 anteriores + 2 nuevos).
- Edge: `python -m unittest edge.test_posture edge.test_fall` → **16 OK** (5 anteriores + 11 nuevos). `edge.smoke` OK con MediaPipe 0.10.35 en Windows (primera ejecución en esta máquina).
- Flutter: `flutter analyze` sin problemas; `flutter test` **19 OK**.
- Ruff en archivos nuevos o modificados de `edge/`: sin hallazgos. En `web/CuidadosApp` persisten los I001 previos, ninguno nuevo.

## Límites y fallos

- No se midió sensibilidad, falsos positivos, latencia de alerta ni inferencia con personas: requiere el protocolo de `edge/README.md` con video o cámara autorizados.
- `edge.run` no se ejecutó en vivo (sin cámara autorizada ni nodo vinculado en un servidor de prueba).
- La latencia hasta el teléfono depende de la frecuencia de `send_mobile_reminders` (P-012-01) y de FCM real (no configurado).

## Aplicación y reversión

Migración `0007_postureobservation_risk_fall` (solo `choices`); no se aplicó en ninguna base real. Reversión: `migrate CuidadosApp 0006`.

## Ajustes 2026-10-25 — push inmediato, texto genérico y QA técnicos

Rama `feature/012-push-inmediato-qa` (desde la 013), commits `e1f25c4`, `da04a1d` y `84daf76`. Entorno Windows, datos ficticios.

| RF / hallazgo | Prueba | Obtenido | Estado |
|---|---|---|---|
| RF-012-13 (D-051) | `test_push.ImmediateFallPushTests.test_fall_is_pushed_on_reception_and_not_repeated` (Firebase simulado, `on_commit` ejecutado) | Push al recibir la caída; el comando posterior no lo repite; recibo confirmado | OK (simulado) |
| RF-012-13 (solo caídas) | `test_immobility_waits_for_the_command` | La inmovilidad no se envía de inmediato; el comando la envía una vez | OK |
| RF-012-13/14 | `test_fcm_failure_keeps_node_response_and_command_retries` | Nodo recibe 201 aunque FCM falle; sin recibo; el comando reintenta y envía una vez | OK |
| RF-012-14 (QA-09) | `test_push.ReservationTests` (transacciones reales) | FCM se llama con `in_atomic_block = False`; segunda entrega deduplicada; un fallo libera la reserva; una reserva abandonada expira a los 2 min | OK |
| RF-012-07 (D-058, D-063) | `test_fall_push_uses_existing_channel_once_and_first`, `test_fall_is_pushed_on_reception…`, `test_access.test_push_command_sends_fall_to_family_and_caregiver` | Texto genérico, `visibility=private`, prioridad alta solo en caída; llega a titular, familiar y cuidador | OK (simulado) |
| RF-012-15 (D-057) | `flutter build apk --debug` y manifiesto fusionado | APK compilado; `minSdkVersion="26"` | OK |
| RF-012-16 (QA-16) | `patient_roles_test.dart`: «A fall is titled as a possible fall» | Título «Posible caída» | OK |
| QA-10 | `test_push.DemoSafetyTests`; `check` con `VIGIA_DEMO_HOSTS=8.8.8.8` | Solo loopback o IP privada; host público impide arrancar; clave aleatoria estable en `.mobile-demo/secret_key` (ignorado) | OK |
| QA-19 | `UsuarioApp.tests.ListadoConsultasTests` | Consultas constantes; contra el código anterior la prueba falla (9 → 15) | OK |
| QA-21 | Revisión del árbol | `mobile/android/app/Users/` (vacío, no versionado) eliminado e ignorado | OK |

Regresión: Django **210 OK** (8 nuevas: 7 en `test_push.py` y 1 en UsuarioApp), check y `makemigrations --check` sin cambios, migración aditiva `0009_pushreceipt_confirmed` probada en avance y reversión. Edge **22 OK**. Flutter analyze sin problemas, **23 OK**.

Límites: push solo con Firebase simulado (D-054). El hilo del push inmediato puede perder el envío si el proceso termina justo después de responder; el comando lo reintenta. La latencia de punta a punta (≤ 10 s) sigue **sin medir**. La migración 0009 no se aplicó a ninguna base real.

## Aceptación funcional

Pendiente.
