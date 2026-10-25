# Validación — 014 / Privacidad de datos de salud

Fecha: 2026-10-25. Entorno aislado: Windows 10, `.venv` (web, SQLite en memoria), `.venv-edge-win`, Flutter 3.47.7. Solo datos ficticios.
Referencia de código: rama `feature/014-privacidad`, commits `0870edb`, `58de2f3` y `444d0c3`.
Estado: verificación técnica automática completa y revisión en navegador hecha por el propietario; Android físico probado el 2026-10-25; los dos fallos del inicio de sesión sin política aceptada se corrigieron (T-014-11) y se comprobaron en el teléfono.

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
| RF-014-14 | Flutter `privacy_test.dart`; Android físico 2026-10-25 | Aviso con botón al portal ante `consent_required`; diálogo de consentimiento (paciente o representante con nombre y relación) | Cumple; en Android el aviso no aparecía al iniciar sesión, corregido en T-014-11 y comprobado en el teléfono (ver «Android físico») | OK |

## Regresión de la base

- Web, desde `web/`: `manage.py check` sin problemas (también con `core.mobile_demo_settings`); `makemigrations --check --dry-run` sin cambios; `manage.py test UsuarioApp homeApp PlanesApp CuidadosApp PrivacidadApp --settings=core.test_settings` → **218 OK** (202 de `develop` + 16 en `PrivacidadApp/tests.py`).
- Edge: **22 OK** (sin cambios).
- Mobile: `flutter analyze` sin problemas; `flutter test` → **26 OK** (22 + 4 en `test/privacy_test.dart`).
- Migración `PrivacidadApp.0001_initial`: avance, reversión a `zero` y avance de nuevo en SQLite temporal, sin errores.

## Revisión visual si aplica

2026-10-25: el propietario revisó en la demo (`.mobile-demo/`, migrada y con consentimientos ficticios) política, aceptación, consentimientos, creación de paciente, exportaciones y eliminación de paciente y de cuenta. Resultado: «lo demás que vi estaba bien», con dos observaciones corregidas el mismo día:

1. **Representante sin nombre:** la página se recargaba sin aviso visible. El error salía como error general del formulario, arriba de todo y con clases que la hoja de estilos compilada no incluye. Ahora cada campo vacío muestra su aviso («Indica el nombre del representante.», «Indica la relación con el paciente.»), con prueba.
2. **«Cuenta eliminada» en «Mis cuidados»:** la eliminación funcionaba y el historial lo mostraba, pero el panel no mostraba autoría de ningún registro. Se agregó «Hecho por …» en la agenda y «registrada por …» en la última postura (RF-013-15, T-013-12).

No se registró qué combinaciones de modo claro/oscuro y ancho móvil cubrió.

## Android físico

2026-10-25, ELI NX9 (Android 16), app debug con servidor demo por USB (`adb reverse`). Cuenta `demo_plus`, sin la política aceptada.

- **Falla: sin botón al portal en el login.** Tras `auth/login`, la app pide `me`, recibe 403 `consent_required` y el login solo muestra en rojo «Acepta la política de privacidad en el portal para continuar.». `ConsentRequiredCard` (con «Abrir el portal») solo se muestra en el inicio ([care_home.dart:249](../../mobile/lib/features/home/care_home.dart#L249)), al que no se llega. Reiniciar la app tampoco lo muestra.
- **Falla: segundo intento con 409.** El login ya guardó el token de sesión ([api.dart:140-143](../../mobile/lib/core/api.dart#L140-L143)). Tras aceptar la política en el portal, volver a pulsar «Ingresar» envía `auth/login` con ese token; allauth responde **409 Conflict** y la app muestra «No se pudo completar la operación.». Solo cerrando y reabriendo la app se entra (el token guardado ya es válido). Un usuario no tiene cómo saberlo.
- Aceptación en el portal desde el navegador del teléfono: sin marcar la casilla el formulario no se envía; al marcarla queda `AccountConsent` con versión `2026-10-25` y fecha. OK.
- Consentimiento al crear paciente en la app: diálogo «¿Quién da el consentimiento?»; con representante, nombre y relación vacíos muestran «Completa este campo.»; luego «Confirmar consentimiento». Dos pacientes ficticios creados con `PatientConsent` (alcance cuidado, base titular, versión y autor). El camino de representante no se completó con datos válidos (ese intento tenía una fecha inválida).
- **Ambas fallas corregidas el mismo día (T-014-11)**, con `test/login_consent_test.dart`. Repetido en el teléfono con `demo_free` (sin política aceptada): tras el login aparece el aviso con «Abrir el portal» y «Ya la acepté»; mientras falta aceptar, «Ya la acepté» mantiene el aviso; «Abrir el portal» abre `/privacidad/aceptar/`; tras aceptar y volver, la app se recarga y entra («Hola, demo_free · VIGIA Free») sin otro `auth/login` ni 409 en el log. Queda un detalle previo: bajo el aviso se ve el inicio vacío («Hola,», «Cargando plan» y las acciones rápidas).
- Detalle de uso: si el servidor rechaza el alta (fecha inválida o cupo lleno), el formulario ya se cerró y hay que reescribirlo y repetir el consentimiento. El mensaje de fecha usa el texto por defecto de Django («Introduzca una fecha válida.»).

## Límites y fallos

- Tras los ajustes de la revisión: Django **219 OK**.
- Tras fusionar `develop` con la PR #3 (2026-10-25): conflicto solo en `docs/ESTADO_PROYECTO.md`, resuelto conservando ambas entradas. Django **227 OK**, `makemigrations --check` sin cambios, Edge **22 OK**, Flutter analyze sin problemas y **27 OK**.
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
