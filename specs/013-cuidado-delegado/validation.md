# Validación — 013 / Cuidado delegado

Fecha: 2026-10-25. Entorno aislado: Windows 10, `.venv` (web, SQLite en memoria de `core.test_settings`), `.venv-edge-win` (edge), Flutter 3.47.7. Solo datos ficticios.
Referencia de código: rama `feature/013-cuidado-delegado`, commits `3a6e60d` a `4f39c68`.
Estado: verificación técnica automática completa; revisión visual y prueba en Android físico pendientes.

| RF | Prueba / pasos / comando | Esperado | Obtenido | Estado |
|---|---|---|---|---|
| RF-013-01 | `InvitationTests.test_code_is_single_use_and_stored_hashed`, `test_web_code_page_and_leave` | Código mostrado una vez, solo hash en base | Hash ≠ código; página muestra el código | OK |
| RF-013-02 | `test_code_is_single_use_and_stored_hashed`, `test_web_join_flow_previews_then_confirms`, `test_api_accept_flow` | Vista previa con paciente y rol; vínculo al confirmar | Vista previa sin vínculo; vínculo creado al confirmar (web y API 201) | OK |
| RF-013-03 | `test_expired_and_revoked_codes_share_the_generic_message` | Mismo mensaje para vencido, revocado e inexistente | Mismo mensaje; sin vínculos | OK |
| RF-013-04 | `test_own_and_duplicate_codes_are_rejected_without_consuming` | Rechazo sin consumir el código | El código sigue pendiente y luego lo usa otra cuenta | OK |
| RF-013-05 | `test_failed_attempts_are_limited` | Tras 5 fallos en 15 min, incluso un código válido se rechaza | Rechazado; aceptado al vencer la ventana | OK |
| RF-013-06 | `test_revocation_stops_actions_and_keeps_authorship`, `test_web_code_page_and_leave` | Acción posterior del revocado → 404; autoría conservada | 404 con token emitido antes; autor intacto; renuncia registra fecha | OK |
| RF-013-07 | `test_web_matrix_by_role` (9 rutas × 5 cuentas), `test_api_matrix_by_role_without_side_effects` (9 endpoints × 5 cuentas + revocar nodo) | 404 sin vínculo (incluido superusuario), 403 rol sin permiso, sin cambios en la base | Según matriz; conteos sin cambio al denegar; nodo ajeno sigue activo | OK |
| RF-013-08 | `test_lists_include_patients_of_two_titulars`, `test_patient_list_reports_role_and_actions` | Listas con pacientes propios y de dos titulares, con rol | Incluidos; rol `cuidador` en la API | OK |
| RF-013-09 | `test_caregiver_is_the_author_and_occurrence_is_recorded_once`, `test_titular_capacity_and_archive_govern_the_caregiver` | Autor = cuidador; ocurrencia única; archivado bloquea al cuidador | Cumple | OK |
| RF-013-10 | `test_links_do_not_use_either_capacity`, `test_lists_include_patients_of_two_titulars` | Cupos sin cambio; cuidador con dos titulares | Conteos 1/1; ve ambos pacientes | OK |
| RF-013-11 | `test_care_reminders_go_to_titular_and_caregiver`, `test_risk_alerts_reach_every_role_on_titular_plan`, `test_push_command_sends_fall_to_family_and_caregiver` (Firebase simulado) | Cuidado → titular y cuidador; riesgo → titular, familiar y cuidador (D-063); nada a ajenos ni tras revocar | Cumple; dos ejecuciones sin duplicados | OK (simulado) |
| RF-013-12 | `test_patient_list_reports_role_and_actions`; Flutter `patient_roles_test.dart` | `allowed_actions` en API; la app oculta acciones y no pide datos no permitidos | Sin token de archivo para el cuidador; la app no llama a historial, observaciones ni nodos | OK |
| RF-013-13 | `test_web_code_page_and_leave`; matriz API (`patients/<pk>/access`); Flutter «Titular manages access» | Lista y gestión solo para el titular | Cumple | OK |
| RF-013-14 | Matriz web/API (historial 403 para el cuidador, `summary` 200); `test_family_configures_but_cannot_archive` | El cuidador ve agenda y última postura, no el historial | Cumple | OK |

## Regresión de la base

- Web, desde `web/`: `manage.py check` sin problemas; `makemigrations --check --dry-run` sin cambios; `manage.py test UsuarioApp homeApp PlanesApp CuidadosApp --settings=core.test_settings` → **202 OK** (181 anteriores + 21 nuevas en `CuidadosApp/test_access.py`). Las pruebas anteriores de dueño único pasan sin cambios.
- Edge: `python -m unittest edge.test_posture edge.test_fall edge.test_run` → **22 OK** (sin cambios en edge).
- Mobile: `flutter analyze` sin problemas; `flutter test` → **22 OK** (19 anteriores + 3 en `test/patient_roles_test.dart`).
- Revisión con `grep` de `owner=`, `patient__owner` y `own_patient(` en CuidadosApp: solo quedan en `capacity.py` y en la selección de cupo (acciones del titular), en `access.py` y en el comando de datos demo. `own_patient` se eliminó.

## Revisión visual si aplica

Pendiente. Las plantillas nuevas (`components/CuidadosApp/access.html`, `pages/CuidadosApp/access_code.html`) y los cambios en ficha y lista renderizan en las pruebas con el cliente de Django, pero no se revisaron en un navegador (claro/oscuro, ancho móvil, teclado). Reutilizan clases CSS existentes; no hizo falta compilar Tailwind.

## Límites y fallos

- Sin prueba en Android físico con dos cuentas (titular y cuidador): depende de T-011-09.
- Push solo con Firebase simulado (D-054 pendiente).
- SQLite no certifica el comportamiento de `select_for_update` bajo concurrencia real; la serialización por titular se verificó por diseño y con pruebas secuenciales.
- El límite de intentos se guarda en la tabla `AccessCodeAttempt`, que crece sin purga; su conservación queda para la spec de privacidad (D-052).
- La app no expone la cámara del teléfono al cuidador (la pestaña Monitoreo exige `detection`), aunque el servidor permite al cuidador enviar observaciones del teléfono (`record`).
- Diferencias con las tareas: el acceso a «Unirme con un código» quedó en la lista de pacientes (web) y en las acciones rápidas (app), no en el menú lateral (T-013-06). La app no usa el endpoint `summary`: el cuidador ve la agenda en la pantalla de inicio y la última postura en la pestaña Reloj (T-013-10).
- Sin fallos introducidos detectados.

## Aplicación y reversión

Migración aditiva `0008_patient_access` (tres tablas, sin cambios de columnas). Probada en SQLite temporal: `migrate` completo, reversión a `0007` y avance de nuevo, sin errores. No se aplicó a ninguna base existente ni se desplegó.

## Aceptación funcional

Pendiente.
