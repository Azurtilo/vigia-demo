# Plan técnico — 014 / Privacidad de datos de salud

Spec: [spec.md](spec.md). Estado: propuesta; sin código.
Autorización de implementación: pendiente.

## Inspección de la base

Leído el 2026-10-25 en `feature/014-privacidad` (desde `develop`, tras la PR #2):

- **Modelos con datos personales o de salud:**
  - `UsuarioApp.Profile`: imagen en `MEDIA_ROOT`, último acceso.
  - `PlanesApp.Subscription`, `SimulatedPaymentMethod` (titular, marca, últimos 4, vencimiento) y `SimulatedOperation`.
  - `CuidadosApp.Patient`: nombre, nacimiento, notas, contacto de emergencia.
  - `CuidadosApp.Medication`, `MedicationTime`, `CareTask`, `CareEvent` (con `snapshot`), `PostureTimer`, `ReminderReceipt`, `CapacitySelection`, `PatientAccess`, `PatientInvitation`, `AccessCodeAttempt`.
  - `CuidadosApp.mobile_models`: `DetectionNode`, `PostureObservation`, `MobileDevice` (token FCM, `session_key`), `PushReceipt`.
  - allauth: `EmailAddress`, `SocialAccount`, `Authenticator` (MFA) y sesiones de Django (también las de `X-Session-Token`).
- **Borrado:** `Patient.owner`, `CareEvent.author`, `ReminderReceipt.user`, `CapacitySelection.user` y los vínculos de la 013 usan `PROTECT`. Además, `CareEvent.corrected_event` es `PROTECT` sobre sí mismo. Hoy no se puede borrar un usuario con pacientes o registros, ni un paciente con datos.
- **Consentimiento y política:** no existe consentimiento, política ni texto legal en plantillas o formularios. Registro: `UsuarioApp.signup_forms.PublicSignupForm`; adaptadores en `UsuarioApp.adapters`.
- **Middleware:** `homeApp.middleware.UpdateLastActivityMiddleware`. API móvil: `CuidadosApp.api.base.MobileView`. Nodo: `api/detection.allowed()`.
- **Logs:** `vigia.edge` registra ids y tiempos, sin datos del paciente.
- **Cambios locales a preservar:** `.claude/skills/`, sin seguimiento. La PR #3 (push inmediato, `PushReceipt.confirmed`) está abierta; la purga de recibos funciona con o sin ese campo.

## Diseño propuesto

**App nueva `PrivacidadApp`.** Concentra la política, los consentimientos, la exportación, la eliminación y la purga. Es transversal y no corresponde a ninguna app existente. Sigue la convención de nombres (`*App`) y se registra en `LOCAL_APPS`. Contiene:

1. **Modelos:**
   - `AccountConsent(user, policy_version, accepted_at)`.
   - `PatientConsent(patient, scope, basis, representative_name, representative_relation, policy_version, recorded_by, recorded_at, revoked_at)`, con un vigente como máximo por paciente y alcance (restricción única condicionada).
   - `PrivacyOperation(kind, created_at, counts JSON)`, sin datos personales (RF-014-13).
2. **Política:**
   - ajuste `PRIVACY_POLICY_VERSION`;
   - plantilla `pages/PrivacidadApp/politica.html`, con el borrador marcado como pendiente de revisión (P-014-04);
   - ruta pública `/privacidad/`.
3. **Puerta de consentimiento de cuenta (RF-014-03):**
   - middleware `PrivacidadApp.middleware.ConsentRequiredMiddleware`, ubicado después de `AccountMiddleware`, que redirige a `/privacidad/aceptar/`;
   - rutas exentas: política, aceptar, cerrar sesión, estáticos, `/_allauth/` y `/api/`;
   - `MobileView.dispatch` responde 403 `{"consent_required": true}` cuando falta la aceptación;
   - `EdgeView` no se afecta, porque el nodo no es una cuenta.
4. **Registro:** `PublicSignupForm` agrega un campo obligatorio «Acepto la política de privacidad» y crea `AccountConsent` al guardar. Las cuentas de Google pasan por la puerta al primer ingreso.
5. **Consentimiento de paciente (RF-014-04..07):**
   - `PatientForm` (web y API) agrega base, nombre y relación del representante solo al crear el paciente;
   - `services.save_patient` crea el consentimiento «cuidado» en la misma transacción;
   - la regla de RF-014-05 vive en `PrivacidadApp.consent.require(patient, scope)`;
   - `require_eligible` la llama para «cuidado»;
   - `api/detection.allowed()` y la vinculación de nodos la llaman para «detección»;
   - la ficha del titular muestra el estado de cada alcance, con acciones para registrar o revocar.
6. **Exportación (RF-014-09/10):**
   - `PrivacidadApp.export`: `account_data(user)` y `patient_data(patient)`, que devuelven diccionarios serializables;
   - vistas POST que descargan `vigia-cuenta-AAAAMMDD.json` y `vigia-paciente-<id>-AAAAMMDD.json` con `Content-Disposition: attachment` y `Cache-Control: no-store`;
   - la del paciente usa `access.patient_for(..., "manage_access")` (solo el titular).
7. **Eliminación (RF-014-11/12):**
   - `PrivacidadApp.erase.delete_patient(user, pk, typed_name)`: bloquea al titular y borra en orden explícito:
     1. observaciones y nodos;
     2. registros, primero las correcciones y luego los originales;
     3. reloj, recibos, horarios, medicamentos y cuidados;
     4. invitaciones, vínculos y consentimientos;
     5. paciente.
   - `erase_account(user, password)`: verifica la contraseña, borra cada paciente propio con `delete_patient`, revoca sus vínculos y borra lo asociado (dispositivos y recibos, sesiones, `EmailAddress`, `SocialAccount`, `Authenticator`, métodos de pago, selección de cupo, recibos de recordatorio, intentos de código, imagen de perfil). Después anonimiza el usuario: `username = "eliminado-<uuid>"`, sin correo ni nombres, `set_unusable_password()`, `is_active = False`.
   - La autoría visible pasa a «Cuenta eliminada», mostrada cuando el autor tiene el prefijo `eliminado-`: un ajuste en `event_data` de la API y en el historial web.
8. **Purga (RF-014-08):**
   - comando `PrivacidadApp/management/commands/purge_expired_data.py` con la tabla `RETENTION` en `PrivacidadApp/retention.py` (P-014-01) y `--dry-run`;
   - cada tipo se borra en su propia transacción;
   - el paciente archivado con plazo vencido se borra con `delete_patient` (como operación del sistema);
   - incluye `clearsessions`.
9. **App móvil (RF-014-14):** `core/api.dart` reconoce `consent_required` y muestra un diálogo con botón al portal (`/privacidad/aceptar/`). El perfil agrega enlaces al portal para exportar y eliminar la cuenta.

## Mapa por requisito

| RF | Archivos existentes / propuestos | Cambio previsto | Evidencia prevista |
|---|---|---|---|
| 01 | Nuevo `PrivacidadApp` (urls, vista, plantilla), `core/urls.py`, `common_settings.py` | Política pública versionada | Prueba: 200 sin sesión con versión visible |
| 02 | `UsuarioApp/signup_forms.py` | Aceptación obligatoria y registro | Prueba de registro con y sin aceptación |
| 03 | Nuevo `middleware.py`, `CuidadosApp/api/base.py` | Puerta web y API | Prueba con versión antigua: redirección, 403 API, cierre de sesión permitido |
| 04 | `CuidadosApp/forms.py`, `services.py`, `api/views.py` | Consentimiento al crear paciente | Prueba de bases titular y representante, y de faltantes |
| 05–07 | Nuevo `consent.py`, `capacity.require_eligible`, `api/detection.py`, ficha web | Bloqueos por alcance y revocación | Pruebas de registro bloqueado, nodo 403 y revocación |
| 08 | Nuevo `retention.py` y comando | Purga por plazo | Prueba con datos vencidos y vigentes de cada tipo, con y sin `--dry-run` |
| 09–10 | Nuevo `export.py`, vistas | JSON de cuenta y de paciente | Pruebas de contenido, ausencia de secretos y 403 a otros roles |
| 11–12 | Nuevo `erase.py`, vistas, `api/views.event_data`, `templates/.../history.html` | Eliminación ordenada y anonimización | Pruebas de eliminación completa, autor anonimizado, sin inicio de sesión y sin avisos |
| 13 | `PrivacyOperation` | Registro sin datos personales | Prueba de que la fila no contiene identificadores |
| 14 | `mobile/lib/core/api.dart`, `features/profile/profile_panel.dart` | Aviso y enlaces | `flutter test` con respuesta `consent_required` |

## Datos y contratos

- Migración inicial de `PrivacidadApp` con los tres modelos nuevos. No altera tablas existentes.
- `PatientForm` agrega campos que no se guardan en `Patient`: `consent_basis`, `representative_name` y `representative_relation`. Solo son obligatorios al crear el paciente.
- API: `POST /api/v1/patients` acepta esos campos. Se agregan `GET`/`POST /api/v1/patients/<id>/consents` (titular) para consultar, registrar o revocar un alcance. Las respuestas 403 por política llevan `consent_required: true`.
- Compatibilidad: un cliente móvil antiguo que crea pacientes sin los campos nuevos recibe un error de validación claro. La app se actualiza en la misma entrega.

## Permisos e interfaz

- Web:
  - política pública;
  - «Aceptar política» con resumen y enlace al texto completo;
  - en el perfil, «Descargar mis datos» y «Eliminar mi cuenta» (confirmación con contraseña);
  - en la ficha, solo para el titular: «Consentimientos», «Descargar datos del paciente» y «Eliminar paciente» (confirmación escribiendo el nombre).
- Reutiliza las plantillas base y el patrón `details.care-archive` para las acciones destructivas.
- Enlace a la política en el pie de las páginas públicas y en el registro.

## Migraciones y reversión

Migración nueva de `PrivacidadApp`, reversible (borra solo sus tablas). No hay cambios de columnas en otras apps. La eliminación de datos no se revierte por diseño. Antes de usarla con datos reales se requiere un respaldo operativo, fuera de esta spec. Probar avance y reversión en una base SQLite temporal.

## Plan de pruebas

- **Django**, nuevo `PrivacidadApp/tests.py`:
  - casos de aceptación de la spec;
  - matriz de permisos de exportar y eliminar (titular, familiar, cuidador, ajeno, superusuario);
  - eliminación de paciente con correcciones encadenadas y vínculos;
  - eliminación de cuenta de titular y de cuidador;
  - purga con fechas manipuladas;
  - JSON sin tokens (`token`, `session_key`, `credential_hash`).
- **Regresión:** suites completas. Las pruebas existentes que crean pacientes deben registrar el consentimiento. Se agrega un helper en las pruebas, para no relajar la regla.
- **Flutter:** respuesta `consent_required` y enlaces del perfil.
- **Manual:** navegador (aceptar política, registrar consentimiento, exportar, eliminar) y Android físico con el aviso de política.

## Riesgos, alternativas y dependencias

- **Riesgo:** la puerta de consentimiento puede bloquear rutas necesarias. Mitigación: lista de rutas exentas probada (cerrar sesión, recuperar contraseña, verificar correo, política, estáticos).
- **Riesgo:** olvidar una tabla en la eliminación. Mitigación: la prueba recorre las relaciones del paciente y del usuario y falla si queda alguna fila que lo referencie.
- **Alternativa descartada:** cambiar `PROTECT` por `CASCADE` en todos los modelos. Facilita borrados accidentales y rompe la autoría de los registros en pacientes ajenos.
- **Alternativa descartada:** borrar la fila del usuario. Exigiría `SET_NULL` en `CareEvent.author` y perdería la distinción entre «cuenta eliminada» y «sin autor».
- **Dependencias:** sin paquetes nuevos. Las pruebas existentes que crean pacientes deben ajustarse para registrar el consentimiento.

## Documentos afectados

`specs/README.md`, `docs/ESTADO_PROYECTO.md`, `docs/TRAZABILIDAD.md`, `docs/DECISIONES.md` (respuestas a P-014-01..04), `docs/CUIDADOSAPP_DESARROLLO.md` y `docs/MOVIL_DESARROLLO.md`. El README debe recordar que el texto de la política es un borrador.

## Decisiones para implementar

P-014-01..04 tienen propuesta por defecto (ver spec). El texto de la política (P-014-04) necesita revisión del propietario antes de presentarse como definitivo. La implementación requiere una instrucción posterior explícita.
