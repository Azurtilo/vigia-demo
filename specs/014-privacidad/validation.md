# Validación — 014 / Privacidad de datos de salud

Fecha: 2026-10-25. Entorno aislado: Windows 10, `.venv` (web, SQLite en memoria), `.venv-edge-win`, Flutter 3.47.7. Solo datos ficticios.
Referencia de código: rama `feature/014-privacidad`, commits `0870edb`, `58de2f3` y `444d0c3`.
Estado: verificación técnica automática completa; revisión en navegador y en Android físico pendientes.

| RF | Prueba | Esperado | Obtenido | Estado |
|---|---|---|---|---|
| RF-014-01 | `PolicyGateTests.test_policy_is_public_and_versioned` | 200 sin sesión con versión y aviso de borrador | Cumple | OK |
| RF-014-02 | `test_signup_requires_acceptance_and_records_it` | Sin aceptar no se crea la cuenta; al aceptar queda registrada | Cumple | OK |
| RF-014-03 | `test_gate_redirects_web_and_blocks_api_until_accepted`, `test_new_policy_version_asks_again`, `test_open_redirect_is_ignored` | Redirección web con `next`; API 403 `consent_required`; política y cierre de sesión accesibles; nueva versión pide aceptar otra vez; `next` externo ignorado | Cumple | OK |
| RF-014-04 | `PatientConsentTests.test_patient_creation_records_who_consents`, `test_api_creation_requires_consent_fields` | Sin consentimiento o representante sin nombre no se crea; con datos completos queda registrado | Cumple (web y API) | OK |
| RF-014-05 | `test_existing_patient_without_consent_is_readable_but_blocked` | Ficha visible; registro rechazado sin crear filas | Cumple | OK |
| RF-014-06 | `test_detection_needs_its_own_consent` | `edge/status` 403 sin consentimiento, 200 con él, 403 tras revocar; vincular nodo 400 con mensaje | Cumple | OK |
| RF-014-07 | `test_revoke_and_register_from_patient_page` | El titular revoca y registra; el cuidador recibe 403 | Cumple | OK |
| RF-014-08 | `PurgeTests.test_purge_deletes_only_expired_and_reports_counts` | `--dry-run` no borra; la ejecución borra solo lo vencido (observaciones, intentos, paciente archivado antiguo); salida y registro sin nombres | Cumple | OK |
| RF-014-09 | `ExportTests.test_account_export_has_no_secrets_nor_foreign_file` | JSON descargable; sin token del dispositivo, `session_key` ni credenciales; registros propios sin la ficha ajena | Cumple | OK |
| RF-014-10 | `test_patient_export_is_titular_only` | Titular descarga; cuidador 403; ajeno 404 | Cumple | OK |
| RF-014-11 | `EraseTests.test_delete_patient_needs_exact_name_and_removes_everything` | Nombre incorrecto rechaza; cuidador 403; nombre correcto (sin importar mayúsculas ni espacios) borra todo, incluida una cadena de correcciones; ninguna fila de ningún modelo apunta al paciente | Cumple | OK |
| RF-014-12 | `test_caregiver_erases_account_and_keeps_anonymous_authorship`, `test_titular_erasure_takes_patients_and_cuts_links` | Contraseña incorrecta no cambia nada; cuenta anonimizada e inactiva, sin correos, sesiones de la app ni inicio de sesión; historial muestra «Cuenta eliminada»; el titular se lleva sus pacientes y vínculos | Cumple | OK |
| RF-014-13 | Exportación, eliminación y purga | `PrivacyOperation` con tipo y cantidades, sin nombres | Cumple | OK |
| RF-014-14 | Flutter `privacy_test.dart` | Aviso con botón al portal ante `consent_required`; diálogo de consentimiento (paciente o representante con nombre y relación) | Cumple | OK |

## Regresión de la base

- Web, desde `web/`: `manage.py check` sin problemas (también con `core.mobile_demo_settings`); `makemigrations --check --dry-run` sin cambios; `manage.py test UsuarioApp homeApp PlanesApp CuidadosApp PrivacidadApp --settings=core.test_settings` → **218 OK** (202 de `develop` + 16 en `PrivacidadApp/tests.py`).
- Edge: **22 OK** (sin cambios).
- Mobile: `flutter analyze` sin problemas; `flutter test` → **26 OK** (22 + 4 en `test/privacy_test.dart`).
- Migración `PrivacidadApp.0001_initial`: avance, reversión a `zero` y avance de nuevo en SQLite temporal, sin errores.

## Revisión visual si aplica

Pendiente: política, aceptación, bloque «Consentimiento y datos» de la ficha, exportaciones, eliminación de paciente y de cuenta, en modo claro y oscuro y en ancho móvil. La demo (`.mobile-demo/`) quedó migrada y con consentimientos ficticios para sus tres pacientes; sus cuentas deberán aceptar la política al entrar.

## Límites y fallos

- **Desviación del plan:** las reglas (puerta de aceptación y consentimiento por paciente) rigen en producción (`PRIVACY_ENFORCED = True` en `common_settings`) y en la demo, pero `core.test_settings` las desactiva para las suites anteriores, que crean usuarios y pacientes sin consentimiento (unas 70 pruebas). `PrivacidadApp/tests.py` las activa con `override_settings`. El plan pedía ajustar todas las pruebas sin relajar la regla. Las altas de cuenta y de paciente sí exigen aceptación y consentimiento siempre, y sus pruebas se actualizaron.
- La purga de recibos de push usa `sent_at`; con la PR #3 fusionada, las reservas sin confirmar también vencen a los 2 minutos por su propio mecanismo.
- `end_sessions` recorre las sesiones vigentes para encontrar las de la cuenta; es adecuado para el volumen del prototipo, no para una base grande.
- La eliminación no alcanza copias de seguridad ni logs del servidor (fuera de alcance).
- El texto de la política es un borrador (D-067) y no certifica cumplimiento de la Ley 21.719 ni de la Ley 20.584.
- Sin fallos introducidos detectados.

## Aplicación y reversión

Migración nueva `PrivacidadApp.0001_initial`, sin cambios en tablas de otras apps. Aplicada solo en la base desechable de la demo. La eliminación de datos no es reversible por diseño. Antes de un uso real, se necesita respaldo operativo y revisión legal.

## Aceptación funcional

Pendiente.
