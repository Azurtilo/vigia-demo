# 013 — Cuidado delegado: familiar y cuidador

Estado: borrador documental. Fecha: 2026-10-25.
Módulo: `CuidadosApp` (web y API), app móvil `mobile/`. Fuente: decisión D-050 del propietario (P-010-02 A) y respuestas del 2026-10-25 sobre cupo, varias familias, revocación e invitación por código.
Implementación autorizada: NO. Revisión del usuario: pendiente.

## Problema y resultado

Hoy cada paciente tiene un único dueño (`Patient.owner`) que lo configura, ejecuta la agenda y ve el historial (009, D-037). El informe supone dos actores: el **familiar** configura y supervisa, y el **cuidador** ejecuta. Sin esa separación, HU-01, HU-02, HU-03 y HU-06 quedan parciales y el cuidado delegado no se puede demostrar (QA-2026-10-22-04).

Resultado esperado: el dueño de un paciente invita con un código a otras cuentas como familiar o cuidador. Cada persona ve y hace solo lo que su rol permite, cada registro guarda a su autor real y el dueño puede revocar el acceso en cualquier momento.

## Actores y permisos

Roles por paciente (no son cargos del portal):

- **Titular**: la cuenta dueña del paciente (`Patient.owner`). Es el familiar responsable: paga el plan, define el cupo y gestiona los accesos. Hay uno por paciente y no cambia en esta spec.
- **Familiar invitado**: otra cuenta con vínculo de rol `familiar`.
- **Cuidador**: otra cuenta con vínculo de rol `cuidador`.
- **Sin vínculo**: cualquier otra cuenta, incluido un vínculo revocado o un superusuario o ADMIN/MANAGER sin vínculo. No hay excepción por cargo para datos clínicos (D-037, D-046).

| Acción sobre un paciente | Titular | Familiar invitado | Cuidador | Sin vínculo / anónimo |
|---|---|---|---|---|
| Ver ficha (nombre, notas, contacto de emergencia) | Sí | Sí | Sí | 404 / 401 |
| Editar ficha | Sí | Sí | No (403) | 404 / 401 |
| Crear paciente | Sí, en su propia cuenta y su cupo | — | — | — |
| Archivar, reactivar, elegir pacientes activos | Sí | No (403) | No (403) | 404 / 401 |
| Crear y editar medicamentos, horarios y cuidados (HU-01) | Sí | Sí | No (403) | 404 / 401 |
| Ver agenda diaria (HU-02) | Sí | Sí | Sí | 404 / 401 |
| Confirmar o marcar omitido un medicamento o cuidado (HU-03) | Sí | Sí | Sí | 404 / 401 |
| Registrar postura y operar el reloj (HU-04) | Sí | Sí | Sí | 404 / 401 |
| Ver historial completo y observaciones de detección (HU-06) | Sí | Sí | No: solo el estado de la agenda del día y la última postura | 404 / 401 |
| Corregir un registro | Sí | Sí | Solo registros propios | 404 / 401 |
| Gestionar nodos de detección | Sí | No (403) | No (403) | 404 / 401 |
| Generar y revocar códigos y vínculos | Sí | No (403) | No (403) | 404 / 401 |
| Renunciar a su propio vínculo | — | Sí | Sí | — |
| Recibir push de cuidado pendiente | Sí | No | Sí | No |
| Recibir push de riesgo (caída, inmovilidad) (HU-05) | Sí | Sí | Sí (D-063) | No |

Reglas comunes:

- Un usuario inactivo no accede (401 en API, 403 en web, como hoy).
- Para un paciente sin acceso se responde 404, no 403, para no revelar que existe. 403 solo cuando la persona tiene vínculo pero su rol no permite la acción.
- Las funciones de plan (detección, alertas de riesgo) dependen de la suscripción del **titular**, no de la cuenta que actúa.
- Un paciente archivado o fuera de la selección de cupo del titular no admite registros de nadie, igual que hoy para el dueño.

## Alcance y exclusiones

Incluye: vínculos paciente–usuario con rol, invitación por código de un solo uso, aceptación, revocación por el titular, renuncia del invitado, matriz de permisos aplicada en web, API móvil y comando de avisos, autor real en cada registro, interfaz web y móvil para gestionar y aceptar accesos, y pruebas de acceso denegado por rol.

No incluye (trabajo futuro): invitación por correo electrónico (D-050 d), traspaso de titularidad, varios titulares por paciente, permisos personalizados por persona, eliminación de cuentas y plazos de conservación (spec de privacidad, D-052).

## Historias y flujo

1. **Invitar.** El titular abre el paciente → «Personas con acceso» → elige rol (familiar o cuidador) → el sistema muestra un código y su vencimiento. El titular lo comparte por fuera del sistema.
2. **Aceptar.** La persona invitada inicia sesión con su propia cuenta (registro web existente, correo verificado) → «Unirme con un código» → ingresa el código → ve el nombre del paciente y el rol → confirma. Desde ese momento el paciente aparece en su lista con su rol.
3. **Operar.** El cuidador ve la agenda y registra medicamentos, cuidados y posturas. Cada registro guarda al cuidador como autor. El familiar configura y revisa el historial, donde ve quién registró cada acción.
4. **Revocar o renunciar.** El titular revoca un vínculo, o el invitado renuncia. El acceso termina de inmediato: el paciente desaparece de la lista de esa persona y cualquier acción pendiente de esa persona sobre el paciente se rechaza. Sus registros anteriores se conservan con su autoría (D-050 c).

Errores relevantes: código vencido, ya usado, revocado o inexistente (mismo mensaje genérico); el titular intenta usar su propio código; la persona ya tiene un vínculo activo con ese paciente; correo sin verificar; demasiados intentos fallidos.

## Requisitos funcionales

- RF-013-01: CUANDO el titular genera una invitación eligiendo el rol `familiar` o `cuidador`, EL SISTEMA crea un código de un solo uso con vencimiento, lo muestra una sola vez y guarda solo su hash.
- RF-013-02: CUANDO una cuenta activa con correo verificado ingresa un código vigente, EL SISTEMA muestra el paciente y el rol, y al confirmar crea el vínculo y marca el código como usado, de forma atómica.
- RF-013-03: SI el código no existe, venció, fue usado o revocado, ENTONCES EL SISTEMA lo rechaza con un mensaje genérico, sin revelar cuál de esos casos ocurrió ni el paciente.
- RF-013-04: SI quien acepta es el titular o ya tiene un vínculo activo con ese paciente, ENTONCES EL SISTEMA rechaza la aceptación sin consumir el código.
- RF-013-05: SI una cuenta acumula más intentos fallidos de código que el límite en la ventana definida, ENTONCES EL SISTEMA rechaza nuevos intentos hasta que termine la ventana.
- RF-013-06: CUANDO el titular revoca un vínculo o un código pendiente, o el invitado renuncia, EL SISTEMA termina el acceso de inmediato, registra fecha y autor de la revocación y conserva los registros anteriores con su autoría.
- RF-013-07: EL SISTEMA aplica la matriz de permisos en servidor a toda vista web, endpoint de la API móvil y de detección que reciba un paciente, respondiendo 404 sin vínculo y 403 con vínculo sin permiso para la acción.
- RF-013-08: Las listas de pacientes, el panel, la agenda y los recordatorios incluyen los pacientes propios y los vinculados, e indican el rol de la persona en cada uno.
- RF-013-09: CUANDO un familiar o cuidador registra un cuidado, una postura o una corrección, EL SISTEMA guarda a esa persona como autor y aplica el cupo, el estado archivado y las funciones de plan del titular.
- RF-013-10: Los vínculos de familiar y cuidador no cuentan en el cupo del titular ni en el cupo propio del invitado (D-050 a). Un cuidador puede tener vínculos con pacientes de distintos titulares (D-050 b).
- RF-013-11: EL SISTEMA envía los avisos de cuidado pendiente al titular y a los cuidadores con acceso vigente, y los avisos de riesgo (caída, inmovilidad) al titular, a los familiares y a los cuidadores con acceso vigente, siempre según las funciones del plan del titular y sin duplicar por dispositivo.
- RF-013-12: La API móvil informa por paciente el rol y las acciones permitidas. La app muestra u oculta las acciones según esa respuesta, sin reemplazar el control del servidor.
- RF-013-13: El titular ve en la web y en la app la lista de personas con acceso (nombre, rol, fecha de aceptación) y de códigos pendientes, y puede revocarlos.
- RF-013-14: El cuidador ve, en lugar del historial completo, el estado de la agenda del día y la última postura registrada del paciente.

## Datos y reglas

**Vínculo** (`PatientAccess`): paciente, usuario, rol (`familiar` | `cuidador`), invitación de origen, aceptado en, revocado en, revocado por. Como máximo un vínculo activo (sin revocar) por paciente y usuario. El titular no puede tener vínculo con su propio paciente. Los vínculos revocados se conservan como historial de accesos.

**Invitación** (`PatientInvitation`): paciente, rol, hash del código, creada por, creada en, vence en, usada en, usada por, revocada en. Reglas propuestas, ajustables antes de implementar:

- Código de 10 caracteres de un alfabeto sin caracteres ambiguos (≈ 50 bits), mostrado en grupos para dictarlo.
- Vigencia de 48 horas y un solo uso.
- Máximo 5 invitaciones pendientes por paciente.
- Límite de 5 intentos fallidos por cuenta cada 15 minutos.

**Registros existentes**: `CareEvent.author` ya existe y pasa a ser la persona que actúa. No se agregan campos a `Patient` ni a `CareEvent`. La autoría visible en el historial usa el nombre completo de la cuenta y, si no lo tiene, el nombre de usuario (comportamiento actual).

**Auditoría de accesos**: creación, aceptación, revocación y renuncia quedan con fecha y autor en los propios modelos. No se registran códigos en claro ni datos clínicos en logs.

## Criterios de aceptación

| RF | Dado / cuando | Entonces |
|---|---|---|
| RF-013-01/02 | Titular genera un código de cuidador; otra cuenta verificada lo ingresa y confirma | Vínculo activo; el paciente aparece en la lista del cuidador con rol «Cuidador»; el código no se puede volver a usar |
| RF-013-03 | Código vencido, usado, revocado o inventado | Mismo mensaje genérico; sin vínculo nuevo |
| RF-013-04 | El titular ingresa su propio código, o un cuidador ya vinculado ingresa otro código del mismo paciente | Rechazo; el código sigue vigente |
| RF-013-05 | Seis códigos inválidos en 15 minutos | El sexto y siguientes se rechazan aunque sean válidos, hasta que termine la ventana |
| RF-013-06 | Titular revoca al cuidador mientras este tiene la agenda abierta | La siguiente acción del cuidador recibe 404; sus registros previos siguen en el historial con su nombre |
| RF-013-07 | Cuidador intenta editar un medicamento, archivar o ver el historial completo por URL directa o API | 403 sin cambios en la base |
| RF-013-07 | Cuenta sin vínculo, superusuario o ADMIN prueba el ID de un paciente ajeno en cada endpoint | 404 sin cambios en la base |
| RF-013-09 | Cuidador confirma un medicamento | `CareEvent.author` es el cuidador; la ocurrencia no se duplica si el titular confirma la misma toma |
| RF-013-09 | El titular baja a Free y el paciente queda fuera de su selección de cupo | Ni el titular ni el cuidador pueden registrar cuidados de ese paciente |
| RF-013-10 | Titular Free (1 paciente) invita a dos cuidadores; un cuidador con su propio paciente Free acepta | Ninguno de los dos cupos cambia |
| RF-013-10 | Cuidador acepta códigos de dos titulares distintos | Ve ambos pacientes, cada uno con las reglas de su titular |
| RF-013-11 | Caída en un paciente de titular Premium con un familiar y un cuidador vinculados | Push de riesgo al titular, al familiar y al cuidador, una vez por dispositivo; cuidado vencido avisa al titular y al cuidador, no al familiar; tras revocar al cuidador, ya no recibe ninguno |
| RF-013-12 | Cuidador abre el paciente en la app | No ve botones de editar ficha, archivar, medicamentos ni accesos; si fuerza la llamada, recibe 403 |
| RF-013-14 | Cuidador abre el paciente | Ve la agenda del día y la última postura, sin historial completo ni observaciones |

## No funcionales

- Privacidad: el código no se guarda en claro ni se escribe en logs; los mensajes de error no revelan si un paciente existe; ningún dato clínico en logs. Preserva «sin video a la nube».
- Seguridad: control en servidor en cada acción (la interfaz solo oculta); rechazo por revocación efectivo en la siguiente petición.
- Usabilidad: código legible en voz alta, rol explicado en palabras simples, confirmación antes de revocar. Español es-CL.
- No se fijan SLA ni métricas de desempeño nuevas.

## Compatibilidad

- Pacientes y cuentas existentes siguen igual: sin vínculos, el titular conserva todas las acciones actuales y la app actual sigue funcionando.
- Se preservan los cupos y la selección de 009 (D-040), los planes de D-038/D-055, la autenticación de D-056, el contrato del nodo (010, 012) y la idempotencia de `CareEvent`.
- Sustituye, para los pacientes con vínculos, la propiedad única de D-037. Relacionadas: [009](../009-cuidados-cuidadores/spec.md), [010](../010-aplicacion-movil/spec.md) (RF-010-08 pasa a esta spec), [012](../012-deteccion-caidas/spec.md) (destinatarios del push de riesgo).

## Supuestos y decisiones pendientes

Supuestos técnicos reversibles: vigencia, longitud y límites del código indicados en «Datos y reglas».

Decisiones resueltas por el propietario el 2026-10-25 ([DECISIONES.md](../../docs/DECISIONES.md)):

- **P-013-01 → D-061**: el familiar invitado puede hacer lo mismo que el titular, salvo archivar pacientes, gestionar el cupo, los nodos y los accesos.
- **P-013-02 → D-062**: el cuidador no ve el historial completo, solo la agenda del día y la última postura.
- **P-013-03 → D-063**: el push de caída o inmovilidad también llega al cuidador, que suele estar en el domicilio y podría reaccionar antes. Amplía HU-05, que nombra solo al familiar.

Sin decisiones pendientes.

## Revisión y cambios

2026-10-25: creada en fase DOCUMENTAR a partir de D-050. Sin aprobación ni autorización de implementación.

2026-10-25 (posterior): el propietario responde P-013-01..03 (D-061 a D-063). P-013-03 cambia la propuesta: el cuidador también recibe el push de riesgo (matriz, RF-013-11 y su criterio de aceptación actualizados). Sigue sin autorización de implementación.
