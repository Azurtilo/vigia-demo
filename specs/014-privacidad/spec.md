# 014 — Privacidad de datos de salud

Estado: borrador documental. Fecha: 2026-10-25.
Módulo: app nueva `PrivacidadApp` (propuesta) y ajustes en `UsuarioApp`, `CuidadosApp` y la app móvil. Fuente: decisión D-052 del propietario (QA-2026-10-22-05, opción A): «Spec de privacidad: consentimiento (versión, fecha, titular o representante), plazo de conservación por tipo de dato, comando de purga, exportación y eliminación de cuenta».
Implementación autorizada: NO. Revisión del usuario: pendiente.

## Problema y resultado

VIGIA guarda datos personales y de salud: nombre y fecha de nacimiento del paciente, contacto de emergencia, medicamentos y dosis, registros de cuidado, posturas, caídas, cuentas, dispositivos y métodos de pago simulados. Hoy no registra consentimiento, no tiene política de privacidad, no fija plazos de conservación y no permite exportar ni eliminar datos. Además, las relaciones `on_delete=PROTECT` impiden borrar a un usuario que tenga pacientes o registros (QA-2026-10-22-05).

Resultado esperado: cada cuenta acepta una política versionada; cada paciente tiene un consentimiento registrado (del propio paciente o de su representante) antes de que se registren datos de salud o se active la detección; los datos vencidos se purgan con un comando; cada persona puede descargar sus datos y eliminar su cuenta; el titular puede eliminar un paciente y todos sus datos.

Marco de referencia: la Ley 21.719 (protección de datos personales; los datos de salud son sensibles) y la Ley 20.584 (derechos de los pacientes). Esta spec no es asesoría legal ni certifica cumplimiento: el texto de la política y los plazos requieren revisión del propietario y, antes de un uso con personas reales, de un especialista.

## Actores y permisos

| Acción | Anónimo | Titular | Familiar / cuidador | Cargos del portal (ADMIN, MANAGER) | Superusuario |
|---|---|---|---|---|---|
| Leer la política de privacidad | Sí | Sí | Sí | Sí | Sí |
| Aceptar la política de su cuenta | — | Sí | Sí | Sí | Sí |
| Registrar o revocar el consentimiento de un paciente | No | Sí | No | No (sin excepción clínica) | No |
| Exportar sus datos de cuenta | No | Sí | Sí | Sí | Sí |
| Exportar los datos de un paciente | No | Sí, de sus pacientes | No | No | No |
| Eliminar un paciente y todos sus datos | No | Sí, de sus pacientes | No | No | No |
| Eliminar su propia cuenta | No | Sí | Sí | Sí | Sí |
| Ejecutar el comando de purga | — | — | — | Operación del servidor, no web | Operación del servidor |

Un usuario inactivo no accede. Sin vínculo con el paciente, 404 (spec 013). La gestión administrativa de cuentas (004/006) no da acceso a datos clínicos.

## Alcance y exclusiones

Incluye: política versionada y su aceptación por cuenta; consentimiento por paciente con titular o representante y alcance (cuidado, detección); bloqueo de registros sin consentimiento vigente; plazos de conservación por tipo de dato y comando de purga con simulación; exportación JSON de la cuenta y de cada paciente; eliminación de paciente; eliminación de cuenta con anonimización de lo que deba conservarse; aviso en la app móvil cuando falte aceptar la política.

No incluye (futuro): cifrado de la base en reposo y migración a PostgreSQL gestionado; registro de actividad de lectura (quién vio qué); designación de encargado de datos y procesos formales ante la autoridad; transferencia de titularidad de un paciente; exportación en PDF; purga de logs del servidor y de copias de seguridad.

## Historias y flujo

1. **Cuenta nueva.** En el registro (correo o Google) la persona acepta la política vigente. Sin aceptarla no puede usar el portal ni la API.
2. **Cuenta existente o política nueva.** Al entrar, si no aceptó la versión vigente, ve la política y la acepta antes de continuar. La app móvil recibe un aviso y abre el portal para aceptarla.
3. **Paciente.** Al crear un paciente, el titular indica quién da el consentimiento (el propio paciente o un representante, con nombre y relación) y confirma el alcance «datos de cuidado». Para vincular una cámara confirma además el alcance «detección». El titular puede revocar un alcance: desde ese momento no se aceptan registros nuevos de ese tipo y se le ofrece eliminar los datos.
4. **Exportar.** Desde su perfil, cualquier persona descarga un archivo JSON con sus datos de cuenta. El titular descarga además, desde la ficha, el JSON completo de un paciente.
5. **Eliminar un paciente.** El titular escribe el nombre del paciente para confirmar; se borran el paciente y todos sus datos, incluidos los registros hechos por cuidadores.
6. **Eliminar la cuenta.** La persona confirma con su contraseña. Se eliminan sus pacientes (como en el paso 5), sus dispositivos, sesiones, métodos de pago y datos de perfil; los registros que hizo en pacientes de otros titulares se conservan con un autor anonimizado («Cuenta eliminada»).
7. **Purga.** El servidor ejecuta periódicamente el comando de purga, que borra lo vencido según la tabla de plazos y reporta solo cantidades.

## Requisitos funcionales

- RF-014-01: EL SISTEMA publica una política de privacidad con versión y fecha, legible sin iniciar sesión.
- RF-014-02: CUANDO una cuenta se registra, EL SISTEMA exige aceptar la política vigente y guarda versión, fecha y cuenta.
- RF-014-03: SI una cuenta autenticada no aceptó la versión vigente, ENTONCES el portal la redirige a aceptarla antes de cualquier otra página interna y la API responde 403 con `consent_required: true`, salvo cerrar sesión, leer la política y aceptarla.
- RF-014-04: CUANDO el titular crea un paciente, EL SISTEMA exige registrar el consentimiento de alcance «cuidado» con base `titular` (el propio paciente) o `representante` (nombre y relación obligatorios), versión de la política, fecha y cuenta que lo registra.
- RF-014-05: SI un paciente no tiene consentimiento vigente de alcance «cuidado», ENTONCES EL SISTEMA permite consultar su ficha pero rechaza registros nuevos de cuidado, medicamentos y posturas y la configuración de horarios.
- RF-014-06: SI un paciente no tiene consentimiento vigente de alcance «detección», ENTONCES EL SISTEMA rechaza vincular nodos, rechaza observaciones del nodo (403, el nodo se detiene por fail-closed) y del teléfono.
- RF-014-07: CUANDO el titular revoca un alcance, EL SISTEMA registra la fecha de revocación, aplica RF-014-05 o RF-014-06 desde ese momento y conserva los datos hasta que el titular los elimine o venzan.
- RF-014-08: El comando `purge_expired_data` borra los datos vencidos según la tabla de plazos, admite `--dry-run` y reporta solo cantidades por tipo, sin datos personales.
- RF-014-09: CUANDO una persona pide exportar su cuenta, EL SISTEMA entrega un JSON con sus datos de cuenta, consentimientos, vínculos, dispositivos (sin tokens), suscripción y métodos de pago simulados (sin datos de tarjeta más allá de marca y últimos 4) y los registros que hizo como autor (fecha, tipo y etiqueta, sin la ficha del paciente ajeno).
- RF-014-10: CUANDO el titular pide exportar un paciente, EL SISTEMA entrega un JSON con la ficha, consentimientos, medicamentos y horarios, cuidados, registros con autor, reloj, observaciones y nodos (sin credenciales).
- RF-014-11: CUANDO el titular confirma la eliminación de un paciente escribiendo su nombre, EL SISTEMA borra en una transacción el paciente y todos sus datos dependientes y libera el cupo.
- RF-014-12: CUANDO una persona confirma con su contraseña la eliminación de su cuenta, EL SISTEMA, en una transacción: elimina sus pacientes como en RF-014-11; revoca sus vínculos; borra dispositivos, sesiones, tokens de la app, direcciones de correo, cuentas sociales, factores MFA, métodos de pago e imagen de perfil; y anonimiza la cuenta (nombre de usuario aleatorio, sin correo ni nombre, contraseña inutilizable, inactiva). Los registros que hizo en pacientes ajenos quedan con autor «Cuenta eliminada».
- RF-014-13: La exportación y la eliminación registran fecha y tipo de operación sin datos personales, para trazabilidad.
- RF-014-14: La app móvil muestra un aviso claro cuando la API responde `consent_required` y abre el portal para aceptar la política; para exportar o eliminar la cuenta enlaza al portal.

## Datos y reglas

**Consentimiento de cuenta** (`AccountConsent`): cuenta, versión de política, aceptado en. Una fila por versión aceptada.

**Consentimiento de paciente** (`PatientConsent`): paciente, alcance (`cuidado` | `deteccion`), base (`titular` | `representante`), nombre y relación del representante (obligatorios si la base es `representante`), versión de política, registrado por, registrado en, revocado en. Como máximo uno vigente por paciente y alcance.

**Plazos de conservación** — propuesta P-014-01, a confirmar por el propietario:

| Dato | Plazo propuesto | Desde |
|---|---|---|
| Intentos fallidos de código (`AccessCodeAttempt`) | 24 horas | El intento |
| Invitaciones usadas, vencidas o anuladas | 90 días | Uso, vencimiento o anulación |
| Recibos de aviso (`ReminderReceipt`, `PushReceipt`) | 30 días | El envío |
| Observaciones sin riesgo | 30 días | La observación |
| Observaciones con riesgo (caída, inmovilidad) | 1 año | La observación |
| Registros de cuidado, medicamentos, cuidados y reloj de un paciente archivado | 2 años | El archivo |
| Sesiones vencidas | Al vencer | Vencimiento (`clearsessions`) |
| Cuentas inactivas sin pacientes ni registros | Sin purga automática en esta versión | — |

Mientras un paciente esté activo, sus registros de cuidado se conservan: son la trazabilidad del cuidado delegado (HU-03, HU-06). Los vínculos revocados se conservan mientras exista el paciente, para mantener la autoría.

**Anonimización de cuenta**: se conserva la fila de usuario solo para que los registros ajenos mantengan un autor; no queda ningún dato que identifique a la persona.

## Criterios de aceptación

| RF | Dado / cuando | Entonces |
|---|---|---|
| RF-014-02 | Registro sin marcar la aceptación | Error de formulario; no se crea la cuenta |
| RF-014-03 | Cuenta que aceptó la versión 1 y la vigente es la 2 | Portal redirige a aceptar; API 403 `consent_required`; cerrar sesión funciona |
| RF-014-04 | Crear paciente con base `representante` sin nombre | Error; no se crea el paciente |
| RF-014-05 | Paciente existente sin consentimiento | Ficha visible; registrar medicamento o postura → rechazo con mensaje |
| RF-014-06 | Consentimiento de detección revocado con nodo activo | `edge/status` 403; observación rechazada; vincular nodo rechazado |
| RF-014-08 | Datos vencidos y vigentes de cada tipo; `--dry-run` | Reporta cantidades sin borrar; sin `--dry-run` borra solo lo vencido |
| RF-014-09/10 | Exportar cuenta del cuidador y paciente del titular | JSON válido con lo indicado; sin tokens, credenciales ni datos de otro titular |
| RF-014-10/11 | Familiar o cuidador intenta exportar o eliminar el paciente | 403; sin cambios |
| RF-014-11 | Titular confirma con un nombre distinto | Rechazo; sin cambios |
| RF-014-11 | Titular confirma con el nombre correcto | Paciente y todos sus datos eliminados; cupo liberado |
| RF-014-12 | Cuidador elimina su cuenta | Sus registros en el paciente ajeno muestran «Cuenta eliminada»; no puede iniciar sesión; sus dispositivos no reciben avisos |
| RF-014-12 | Titular con pacientes vinculados a un cuidador elimina su cuenta | Sus pacientes y datos se eliminan; el cuidador deja de verlos |
| RF-014-12 | Contraseña incorrecta | Rechazo; sin cambios |
| RF-014-14 | API responde `consent_required` en la app | Aviso con botón al portal |

## No funcionales

- Las exportaciones y eliminaciones no escriben datos personales en logs.
- Sin video a la nube: se preserva.
- La política se redacta en español claro (es-CL) y se presenta como borrador del prototipo hasta su revisión.
- No se declara cumplimiento de la Ley 21.719 ni de la Ley 20.584.

## Compatibilidad

- Preserva cuentas y planes (004/006/007), cuidados y cupos (009), app y nodo (010–012) y vínculos (013).
- Sustituye, para la eliminación explícita, la protección por `PROTECT`: la eliminación se hace con un servicio ordenado, y `PROTECT` sigue impidiendo borrados accidentales fuera de ese servicio.
- Datos existentes de las demos: quedan sin consentimiento y se aplica RF-014-05/06 (P-014-03).

## Supuestos y decisiones pendientes

Supuestos técnicos reversibles: versión de política en un ajuste `PRIVACY_POLICY_VERSION`; exportación en JSON; anonimizar en vez de borrar la fila de usuario.

Decisiones para el propietario:

- **P-014-01** — Plazos de conservación. Propuesta: la tabla de «Datos y reglas».
- **P-014-02** — Qué pasa con los pacientes al eliminar la cuenta del titular. Propuesta: se eliminan con todos sus datos y los vínculos se cortan. Alternativa futura: traspasarlos a un familiar.
- **P-014-03** — Pacientes existentes sin consentimiento. Propuesta: ficha visible, registros nuevos bloqueados hasta que el titular registre el consentimiento. Alternativa: periodo de gracia.
- **P-014-04** — Texto de la política. Propuesta: borrador redactado en esta spec para el prototipo, marcado como pendiente de revisión legal antes de usar datos reales.

## Revisión y cambios

2026-10-25: creada en fase DOCUMENTAR a partir de D-052. Sin aprobación ni autorización de implementación.
