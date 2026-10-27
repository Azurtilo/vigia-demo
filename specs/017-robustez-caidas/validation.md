# Validación — 017 / Robustez de la detección de caídas

Entorno: Windows 10, rama `feature/017-robustez-caidas` desde `develop` (`2fedd78`). Web con `.venv` raíz y `core.test_settings` (SQLite en memoria). Edge con `.venv-edge-win` (MediaPipe 0.10.35, OpenCV 5.0.0.93) y modelo en `edge/models/`. Flutter 3.47.7.
Estado: verificación técnica **sintética**. Sin cámara real, servidor en vivo, personas ni Firebase real (T-017-13).

## Línea base (T-017-01), 2026-10-27

| Comando | Resultado |
|---|---|
| `manage.py check --settings=core.test_settings` | Sin problemas |
| `manage.py makemigrations --check --dry-run --settings=core.test_settings` | Sin cambios |
| `manage.py test UsuarioApp homeApp PlanesApp CuidadosApp PrivacidadApp --settings=core.test_settings` | **235 OK** |
| `python -m unittest edge.test_posture edge.test_fall edge.test_run` | **22 OK** |
| `flutter analyze` / `flutter test` | Sin problemas / **46 OK** |
| `python -m edge.bench sintetico.mp4` (300 cuadros de ruido, 640×480, 30 FPS, en el scratchpad de la sesión) | 0 personas; inferencia promedio 12,31 ms, p95 13,56 ms, máx 20,31 ms; 57,71 FPS; 0 caídas. **No mide el KPI** (sin persona en el cuadro) |

## Resultado final (T-017-12), 2026-10-27

| Comando | Resultado |
|---|---|
| `manage.py check` / `makemigrations --check --dry-run` | Sin problemas / sin cambios |
| Suite Django (5 apps) | **246 OK** (+11) |
| `python -m unittest edge.test_posture edge.test_fall edge.test_run` | **56 OK** (+34) |
| `python -m edge.smoke` | Modelo cargado, imagen vacía sin falsas personas |
| `flutter analyze` / `flutter test` | Sin problemas / **51 OK** (+5) |
| `dart format --set-exit-if-changed` en los archivos Dart tocados | Sin cambios |
| `ruff check` en los archivos Python nuevos (`edge/bed.py`, `edge/monitoring.py`, `edge/options.py`) | Sin hallazgos. En los archivos existentes tocados, los mismos hallazgos que antes (I001, SIM117, F401 previos); ninguno nuevo |
| CI de la [PR #12](https://github.com/Azurtilo/vigia-demo/pull/12) (GitHub Actions) | Verde: Django, Edge, Flutter y `pip-audit` |
| Migración `0010_detectionnode_monitor_state` con `core.test_settings` | Avance: columnas creadas; reversión a `0009`: columnas eliminadas; avance otra vez: OK |

## Evidencia por requisito

| RF | Prueba | Obtenido | Estado |
|---|---|---|---|
| RF-017-01 | `edge.test_fall.BedZoneTests` (4): menos de 3 o más de 8 vértices, fuera de 0–1, `True`, NaN, colineales, archivo con clave extra, esquinas cruzadas, borde y esquina dentro, `--bed-settings` + `--bed-lying-seconds` | OK | Verificado (sintético). Calibración con ventana: solo revisión de código (no escribe imágenes); en vivo en T-017-13 |
| RF-017-02 | `test_slow_slide_out_of_bed_is_a_fall_the_impact_rule_misses`, `test_lying_outside_long_after_walking_is_a_fall`, `test_upright_or_sitting_outside_the_bed_is_not_a_fall`, `test_lying_outside_briefly_and_getting_up_is_not_a_fall` | Deslizamiento: 1 caída entre 7,5 y 8,5 s; la regla de impacto, ninguna. Sentado 60 s fuera y 3 s acostado: ninguna | Verificado (sintético) |
| RF-017-03 | `test_shape_appearing_on_the_floor_is_treated_as_no_person`, `test_teleport_breaks_the_track` | Sin caída; resultado «sin persona» | Verificado (sintético) |
| RF-017-04 | `test_covered_hips_fall_back_to_shoulders_without_a_jump`, `test_only_the_head_outside_the_bed_is_unknown` | Caída con hombros; solo cabeza → sin caída | Verificado (sintético) |
| RF-017-05 | `edge.test_fall.test_back_in_bed_or_upright_rearms`; `edge.test_run.BedMonitorTests` (6) | Un solo `fall-v1` cuando cumplen ambas reglas (el de cama queda en el log como «ya avisada»); dos caídas con 3 s de pie; cuadros sueltos no rearman; sin zona de cama, igual que la 012 | Verificado (sintético) |
| RF-017-06 | `MonitorStatusTests.test_person_lost_after_being_seen_and_back`, `test_never_seen_is_not_lost`; `MonitorStateTests.test_two_people_in_view_are_not_lost`, `test_sheet_on_the_floor_counts_as_no_person` | Perdida a los 10 s tras haber sido vista; nunca vista: sin estado; dos personas: `normal` | Verificado (sintético) |
| RF-017-07 | `test_no_image_while_frames_stop_and_recovery`, `test_no_frame_at_all_from_start`; `CameraTests` (2); `test_lease_pause_is_not_a_blind_camera` | `sin_imagen` a los 10 s y vuelta a `normal`; reapertura con esperas de 1, 2, 4 y 8 s; un video local termina; la pausa por lease no es `sin_imagen` | Verificado (simulado). Cámara real desconectada: T-017-13 |
| RF-017-08 | `test_low_light_with_hysteresis`, `test_priority_no_image_then_low_light_then_lost` | `poca_luz` y `normal`; oscilación en 0,11/0,13 sin cambios; con poca luz, 0,13 no basta para volver | Verificado (sintético) |
| RF-017-09 | `MonitorStateUplinkTests` (3); `CuidadosApp.test_mobile.test_node_reports_monitor_state_on_renewal` | Parámetro en cada renovación y renovación adelantada al cambiar; solo lista cerrada; servidor que lo ignora mantiene el lease. Backend: guarda estado y `monitor_since` solo al cambiar; 400 ante valor, parámetro extra o repetido sin tocar `last_seen_at`; nodo sin plan (403) o revocado (401) no cambia | Verificado |
| RF-017-10 | `test_node_reports_monitor_state_on_renewal` (lista de nodos), matriz `test_access` (nodos 200/403/403), `CameraStateTests` (3), `camera_state_test.dart` (4), `patient_roles_test.dart` «Every role sees the camera state read-only» | Titular ve el estado en la tarjeta; titular, familiar y cuidador ven `camera_state` sin nombre, id ni última señal del nodo; ajeno y superusuario 404; `null` sin nodos, sin estado o sin plan; gana el peor estado; nodo callado = `sin_senal` | Verificado. Revisión visual en dispositivo: T-017-13 |
| RF-017-11 | `test_push.NodeAlertTests` (5 de 6), `test_access.test_blind_camera_alert_reaches_every_role` | Un aviso por episodio y dispositivo, texto genérico, visibilidad privada, sin prioridad alta; mismo estado tras `normal` = nuevo aviso; `poca_luz` y estado desconocido sin push; llega a titular, familiar y cuidador | Verificado (Firebase simulado) |
| RF-017-12 | `test_silent_node_alerts_once_and_again_after_reconnecting`, `test_stopped_on_purpose_or_without_risk_alerts_is_silent`, `test_old_episodes_are_not_announced`, `test_falls_go_before_node_alerts` | Aviso a los 60 s, una vez, y otro tras reconectar y volver a callar; nada si está revocado, archivado, sin consentimiento o sin `risk_alerts`; nada si el episodio pasó de 1 h; las caídas van primero | Verificado (Firebase simulado) |
| RF-017-13 | `test_slow_slide_is_sent_by_the_bed_rule_without_coordinates_in_the_log`, `test_two_people_in_view_are_not_lost` (log) | Log con `event_id`, inicio y confirmación, sin coordenadas; cambios de estado en el log | Verificado |
| RF-017-14/15 | Revisión de [edge/README.md](../../edge/README.md) | Secciones de zona de cama, estado de monitoreo, instalación, casos difíciles y protocolo ampliado; enlaces comprobados | Verificado (documental) |

## Mutaciones

Cada mutación se aplicó de forma temporal y se revirtió; las pruebas indicadas fallaron con ella.

| Mutación | Pruebas que fallan |
|---|---|
| Sin control de salto en el seguimiento | `test_shape_appearing_on_the_floor…`, `test_teleport_breaks_the_track` |
| Un hueco sin persona no corta el «de pie» | `test_back_in_bed_or_upright_rearms` (la primera versión de la prueba no lo detectaba; se reescribió) |
| Sin respaldo de hombros | `test_covered_hips_fall_back_to_shoulders…` |
| Sin cerrojo común | 4 pruebas de `BedMonitorTests` |
| Sin rearme | `test_two_falls_with_three_seconds_upright_between` |
| Sin histéresis de luz | `test_low_light_with_hysteresis` |
| La pausa por lease no reinicia el estado | `test_lease_pause_is_not_a_blind_camera` |
| Dos personas cuentan como persona perdida | `test_two_people_in_view_are_not_lost` |
| Avisos de nodo sin `allowed()` | `test_stopped_on_purpose_or_without_risk_alerts_is_silent` |
| Sin límite de 1 h por episodio | `test_old_episodes_are_not_announced` |
| Clave del aviso sin `monitor_since` | `test_blind_states_alert_once_per_episode…` (la primera versión no lo detectaba; se reforzó con el mismo estado dos veces) |
| `poca_luz` con push | `test_low_light_and_unknown_state_are_not_pushed` |

## Rendimiento (RNF inferencia < 100 ms)

Mismo video sintético, sin personas (**no mide el KPI**):

| Medición | Inferencia promedio / p95 | Brillo + regla de cama promedio / p95 |
|---|---|---|
| Línea base (sin cambios de la 017) | 12,31 / 13,56 ms | — |
| Final, sin `--bed-config` (dos corridas) | 11,38–16,90 / 12,09–23,41 ms | — |
| Final, con `--bed-config` (dos corridas) | 11,34–11,69 / 12,04–13,96 ms | 0,48–0,50 / 0,56–0,62 ms |

La corrida de 16,90 ms se hizo mientras corrían en paralelo las suites de Django y Flutter; las demás, en un equipo sin otra carga. El costo de lo agregado (≈ 0,5 ms por cuadro) es menor que la variación entre corridas. Con personas reales, la regla de cama hace más trabajo por cuadro; se mide con el video del protocolo.

## Límites y fallos

- Todo lo anterior es sintético o simulado: no se abrió una cámara, no se ejecutó `edge.run` en vivo, no se probó la calibración con ventana y no hubo push real (Firebase de prueba pendiente, D-054). Va a T-017-13.
- `max_track_speed` (8 troncos/s), `lost_seconds` y `min_brightness` son valores propuestos; se ajustan con el protocolo ampliado (25 caídas y 60 actividades normales, fijado en el README antes de ejecutar).
- La demora de los avisos de nodo depende de la cadencia de `send_mobile_reminders` (5 min propuestos): hasta unos 6 minutos para un nodo apagado.
- Un 400 en la renovación detiene la captura del nodo al vencer el lease. El nodo solo envía valores de su lista cerrada (`test_only_known_states_are_sent`), igual a la del backend.
- La migración `0010` no se aplicó en ninguna base real.

## Prueba funcional de punta a punta, 2026-10-27

A pedido del usuario («haz prueba de funciones, para ver que nada se caiga»). Servidor demo (`core.mobile_demo_settings`) sobre una **copia desechable** de `.mobile-demo/demo.sqlite3` en el scratchpad de la sesión, con la migración `0010` aplicada solo a la copia; la base de la demo original no se modificó. Cuenta ficticia `demo_premium`.

| Fase | Qué se hizo | Resultado |
|---|---|---|
| 1. Flujos existentes | Portal sin sesión (login, privacidad, `/mobile/`, redirecciones), login de la app y API `me`, `capabilities`, `patients`, `agenda`, `reminders`, `guides`, ficha, resumen, medicamentos, historial, observaciones y nodos | **20/20 OK**; la ficha trae `camera_state` (`null` sin nodos) |
| 2. Nodo real | Vincular nodo: primero rechazado por falta de consentimiento de detección (spec 014, correcto); con el consentimiento registrado, 201 y estado `desconocido`. `python -m edge.run` real contra el servidor con un video de 4 s con imagen y 16 s en negro, `--bed-config` y referencias ficticias | El nodo informó `normal` y luego `poca_luz` en la renovación (visto en el log del servidor); inferencia 11,5–11,8 ms; terminó limpio al acabar el video (salida 0) |
| 3. Servidor | Estado del nodo y de la ficha, renovación sin parámetro, con valor inválido, parámetro ajeno y repetido, `sin_imagen`, caída `fall-bed-v1`, reenvío y caída con coordenadas extra, dispositivo ficticio | **16/16 OK** (400 en los inválidos; duplicado deduplicado; caída en el historial) |
| 4. Avisos | Candidatos de `send_mobile_reminders` para el dispositivo ficticio, sin Firebase | Caída primero y luego el aviso de cámara `sin_imagen`. Tras 123 s sin renovar: aviso `offline`, ficha `sin_senal` y tarjeta sin «Conectado». El comando, sin push activado, termina con el error esperado |
| 5. App en Android | APK debug de esta rama en ELI NX9 (Android 16), servidor por USB con `adb reverse` | Login, inicio y ficha cargan. Ficha: «Cámara: Poca luz: el monitoreo no es confiable» con advertencia. Monitoreo: tarjeta «Conectado · Última señal … / Poca luz…» con advertencia y «Posible caída» en el historial |

Límites: sin persona real frente a una cámara, sin calibración con ventana y sin push real (siguen en T-017-13). La app queda instalada en el teléfono con este build de prueba.

## Aplicación y reversión

Migración aditiva `0010_detectionnode_monitor_state` (dos `AddField` con valores por defecto). Reversión: `migrate CuidadosApp 0009`, que pierde solo el último estado informado; la siguiente renovación lo regenera.

## Aceptación funcional

Pendiente.
