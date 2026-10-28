# 019 — Migración a FastAPI + Firebase

Estado: aprobada por el propietario; implementación autorizada por tareas (ver [tasks.md](tasks.md)). Fecha: 2026-10-28.
Cambio transversal: backend, app móvil, portal web y operación. Fuente: revisión del proyecto `vigia 26` de otro integrante del equipo (FastAPI + Firestore + Firebase Auth, app Flutter con Riverpod y go_router, commit `5187922`, 2026-10-28) y respuestas del propietario a la lista de decisiones (sesión del 2026-10-28, D-081..D-097).
Implementación autorizada: SÍ, «concuerdo con tus decisiones, dejamos develop con django y probamos los cambios en una nueva rama, autorizo que cambies codigo pero antes registra todo» (2026-10-28). Sin merge, despliegue ni cuentas reales sin autorización aparte.

## Problema y resultado

VIGIA tiene hoy un backend y portal Django. El equipo decidió que el producto se entregue con **FastAPI + Firebase (Auth, Firestore y FCM)**. Otro integrante ya construyó por su cuenta un backend FastAPI con pruebas y una app Flutter para ese backend, pero sin detección, Edge, alertas, push, recordatorios ni consentimiento, que sí existen en este repositorio.

Resultado: en la rama `feature/019-migracion-firebase`, VIGIA funciona de punta a punta sobre FastAPI + Firebase: el nodo Edge **sin cambios de código** envía una caída y el familiar recibe el push; las HU-01..07 se pueden ejecutar en la app y el portal mínimo; y la evidencia se registra de nuevo en `validation.md`. `develop` conserva Django como respaldo hasta que el propietario autorice la fusión.

## Actores y permisos

Se adoptan los roles por paciente del backend base (dueño, familiar, cuidador; permisos explícitos por membresía) y el rol de cuenta `admin`/`client`. La matriz de acciones nuevas:

| Acción / datos | Anónimo | Dueño | Familiar | Cuidador | Admin de cuenta |
|---|---|---|---|---|---|
| Vincular / revocar nodo Edge | No | Sí (plan con cámara y consentimiento de detección) | No | No | No (no tiene acceso clínico) |
| Ver estado agregado de la cámara | No | Sí | Sí | Sí | No |
| Ver alertas de riesgo y observaciones | No | Sí | Si tiene el permiso | Si tiene el permiso | No |
| Recibir push de riesgo | — | Sí | Si tiene el permiso | Si tiene el permiso | — |
| Registrar consentimiento del paciente | No | Sí | No | No | No |
| Enviar observaciones (`/api/v1/edge/*`) | Solo con token de nodo válido | — | — | — | — |
| Disparar recordatorios (`/internal/tick`) | Solo con el secreto del cron | — | — | — | — |

Sin acceso a un paciente se responde 404 (regla del backend base). Una cuenta suspendida no opera. Los permisos se validan siempre en el servidor; la app solo oculta lo que no corresponde.

## Alcance y exclusiones

**Incluye:** el backend base importado y ampliado con nodos, contrato Edge, observaciones, alertas, push, aviso de cámara ciega y sin señal, reloj de cambio de posición, consentimiento, recordatorios por cron y tokens de dispositivo; la app base importada dentro del proyecto Flutter de este repositorio con nuestras funciones; un portal React mínimo para la HU-07; despliegue sin cuenta de facturación; revalidación y documentos.

**No incluye:** migrar datos de Django (se parte de cero, D-085); pagos reales (D-090); colores en el portal web (trabajo futuro, D-093); push en iOS (sigue D-069); eliminar Django de `develop` (solo con autorización de fusión); cambios al código del Edge.

## Historias y flujo

- **Dueño:** se registra con correo o Google (Firebase Auth), acepta la política, crea el paciente con su consentimiento, configura medicamentos y tareas con el selector de horarios, vincula la cámara y entrega el token al nodo.
- **Cuidador:** se une con un código, ve la agenda de hoy, registra tomas (a tiempo, con retraso y hora real, o no dada con motivo) y cambios de posición, que reinician el reloj.
- **Nodo Edge:** renueva cada 10 s y envía observaciones con el mismo contrato de hoy; una caída genera alerta y push inmediato.
- **Familiar:** recibe el push, abre la alerta y revisa el historial.
- **Cron externo:** cada minuto llama al endpoint interno; el backend envía los recordatorios que correspondan y revisa nodos sin señal.

## Requisitos funcionales

### Backend

- RF-019-01: EL SISTEMA incluye el backend FastAPI base en `backend/`, con sus pruebas pasando contra los emuladores de Firebase.
- RF-019-02: CUANDO el dueño vincula un nodo, EL SISTEMA genera un token aleatorio, lo muestra una sola vez y guarda solo su SHA-256. Hay un nodo activo por paciente y puede revocarse.
- RF-019-03: EL SISTEMA atiende `GET /api/v1/edge/status` y `POST /api/v1/edge/observations` con el contrato vigente de la 010/012/017: `Authorization: Bearer`, `monitor_state` opcional, `lease_seconds` 30, las 7 claves exactas, límites de tiempo, deduplicación por `event_id` (409 si se reutiliza con otros datos), 401 sin token válido y 403 si el monitoreo no está activo (plan, capacidad, consentimiento o revocación).
- RF-019-04: CUANDO llega una observación con `risk = fall`, EL SISTEMA crea una alerta y envía el push sin esperar a otras tareas, con texto genérico, a los miembros con permiso de alertas, si el plan del dueño incluye alertas de riesgo. La inmovilidad crea una alerta y avisa por el ciclo del cron.
- RF-019-05: EL SISTEMA guarda el estado de monitoreo del nodo y avisa «persona no visible» o «sin imagen» (D-074), y «sin señal» si un nodo activo lleva más de 60 s sin renovar (D-075), una vez por episodio.
- RF-019-06: CUANDO se registra un cambio de posición, EL SISTEMA reinicia el reloj del paciente; el reloj y su programación quedan disponibles para la app (equivalente a `timer` y `timer-schedule` de la 011).
- RF-019-07: EL SISTEMA exige aceptar la política vigente antes de operar y el consentimiento del paciente por finalidad (`cuidado`, `deteccion`); sin consentimiento de detección, el nodo recibe 403 (fail-closed, spec 014).
- RF-019-08: CUANDO el cron llama a `POST /internal/tick` con el secreto correcto, EL SISTEMA envía los recordatorios de tomas vencidas no registradas, una vez por toma (identificador `{medId}_{instanteUTC}`), y revisa nodos sin señal. Sin el secreto responde 401 sin hacer nada.
- RF-019-09: EL SISTEMA registra y elimina tokens FCM por dispositivo y usuario.
- RF-019-10: EL SISTEMA acepta observaciones puntuales desde la cámara del teléfono (contrato de `phone-observations`), sin imagen ni coordenadas.
- RF-019-11: EL SISTEMA se mantiene dentro de la cuota gratuita de Firestore para un piloto de 1 nodo y 3 teléfonos: autorización del nodo en memoria hasta 60 s (invalidada al revocar), última señal escrita como máximo cada 30 s y perfil de usuario en memoria hasta 60 s (D-095).

### App móvil

- RF-019-12: La app usa como base el código de la app del backend base (Riverpod, go_router, tema y paleta de `docs/diseno-visual.md`, Nunito), dentro del proyecto Flutter de este repositorio (identificador, Android/iOS, plugin `vigia_pose`, modelo y guías).
- RF-019-13: La barra inferior tiene 5 secciones: Hoy, Pacientes, Alertas, Posturas y Cuenta.
- RF-019-14: Alertas muestra las alertas de riesgo y los avisos de cámara de los pacientes a los que la persona tiene acceso, del más reciente al más antiguo.
- RF-019-15: Posturas reúne el análisis con la cámara del teléfono, el reloj de cambio de posición, la tarjeta del nodo (solo el dueño) y la línea «Cámara: <estado>» (D-077).
- RF-019-16: La app recibe push de riesgo y de recordatorios y programa avisos locales de respaldo con el mismo identificador de toma; al registrar la toma se cancela el aviso local (D-089).
- RF-019-17: La app pide la aceptación de la política y el consentimiento del paciente antes de las funciones que los requieren.
- RF-019-18: La app permite ingresar con correo y contraseña o con Google mediante Firebase Auth.
- RF-019-19: La app consulta el servidor al abrirse, al volver a primer plano, al recibir un push y como máximo cada 5 minutos en primer plano.

### Portal web

- RF-019-20: El portal React permite ingresar con Firebase Auth, ver el plan, simular el cambio y confirmarlo (HU-07), consumiendo la misma API.

### Operación y validación

- RF-019-21: El backend corre en Render (plan gratis) con Firebase Spark, sin cuenta de facturación; credenciales solo en variables del proveedor; los emuladores están prohibidos en producción.
- RF-019-22: El nodo Edge funciona contra el nuevo backend cambiando solo la URL del servidor; `edge.test_*` pasan sin cambios.
- RF-019-23: `validation.md` registra la evidencia de las HU-01..07, RT-01..03 y los RNF con el nuevo backend; lo que no se mida queda «sin evidencia».

### Privacidad (D-098, spec 014)

- RF-019-24: Una vez al día, desde el tick del cron, EL SISTEMA purga lo vencido según los plazos de D-064: intentos de código, 24 h; invitaciones cerradas, 90 días; recibos de recordatorio y de push, 30 días; observaciones sin riesgo, 30 días; con riesgo, 1 año; pacientes archivados, 2 años con todos sus datos. Los registros de cuidado de un paciente activo se conservan. Cada purga deja una operación con conteos, sin datos personales.
- RF-019-25: CUANDO una persona pide sus datos, EL SISTEMA entrega un JSON con su cuenta, consentimientos y lo que registró en pacientes ajenos; el dueño puede exportar además el JSON completo de un paciente. Nunca incluye tokens FCM, hashes de credenciales de nodos ni códigos de invitación.
- RF-019-26: CUANDO el dueño elimina un paciente, escribiendo su nombre para confirmar, EL SISTEMA borra el paciente y todas sus subcolecciones, nodos, invitaciones y membresías.
- RF-019-27: CUANDO una persona elimina su cuenta con un inicio de sesión reciente (`auth_time` de hasta 5 minutos), EL SISTEMA borra sus pacientes como dueño (D-065), retira sus membresías, borra tokens FCM, consentimientos y suscripción, elimina el usuario de Firebase Auth y deja `users/{uid}` solo como autor anónimo de los registros en pacientes ajenos. Sin inicio de sesión reciente responde 401 y no borra nada.

## Datos y reglas

- Se adoptan las colecciones de `docs/modelo-datos.md` del backend base. Se agregan: `edgeNodes/{nodeId}` (dueño, `patientId`, nombre, `credentialHash`, `active`, `lastSeenAt`, `monitorState`, `monitorSince`, avisos enviados por episodio); `patients/{id}/observations/{nodeId|phone}_{eventId}` (ID determinista para deduplicar, 7 claves más la recepción y el hash del contenido); `patients/{id}/alerts/{id}` (`obs_{observación}` o `node_{nodo}_{estado}_{inicio}` por episodio, con `pushPending`); `patients/{id}/timer`; `patients/{id}/consents/{finalidad}` y la aceptación de la política por cuenta; `devices/{installationId}` con el `uid` (una instalación pertenece a una sola cuenta, como en Django; reemplaza `users/{uid}/fcmTokens` del modelo base); `pushReceipts/{sha256(instalación|aviso)}` para no repetir un push; `reminderDeliveries/{patientId}_{medId}_{instanteUTC}` para no repetir avisos.
- Nunca se guardan imágenes, video ni coordenadas del cuerpo.
- Las alertas y el historial se escriben en el mismo lote que la acción que los origina.
- Los planes del backend base (Gratis, Plus y Premium; cámara y alertas en Premium) son la fuente de verdad.

## Criterios de aceptación

| RF | Dado / cuando | Entonces |
|---|---|---|
| RF-019-03 | El Edge sin cambios con un token válido envía una observación de prueba | 201; reenviarla da `duplicate: true`; con otros datos y el mismo `event_id`, 409; con una clave `image`, 400 |
| RF-019-03 | El token fue revocado o el plan no tiene cámara | 401 o 403 según el caso; nunca 201 |
| RF-019-04 | Llega una caída | Alerta creada y push solicitado a los destinatarios con permiso; ningún dato clínico en el texto |
| RF-019-07 | El paciente no tiene consentimiento de detección | Vincular nodo rechazado y renovación del nodo con 403 |
| RF-019-08 | El cron llama dos veces en el mismo minuto | Un solo recordatorio por toma; sin secreto, 401 |
| RF-019-11 | Un día con 1 nodo renovando cada 10 s | Lecturas estimadas por la prueba de presupuesto bajo 50.000 y escrituras bajo 20.000 |
| RF-019-13 | La app en un teléfono de ~360 dp | 5 secciones visibles sin cortar etiquetas |
| RF-019-24 | Una observación sin riesgo de hace 31 días y otra con riesgo de hace 31 días | La primera se purga, la segunda se conserva |
| RF-019-25 | Exportación de un familiar | Incluye sus registros en el paciente ajeno, no la ficha de ese paciente; sin tokens ni hashes |
| RF-019-27 | Eliminar la cuenta con un inicio de sesión de hace 10 minutos | 401 y nada borrado; con uno reciente, pacientes propios borrados y registros en pacientes ajenos con autor anónimo |
| RF-019-22 | **Punto de control de la semana 1** | Nodo real → caída → push recibido en Android. Si no se cumple el 2026-11-04, se informa al propietario para volver a Django en la entrega (D-081) |

## No funcionales

- Alerta de caída ≤ 10 s, inferencia < 100 ms, caídas ≥ 90 % con FP ≤ 5 % y disponibilidad ≥ 99,5 % siguen siendo **objetivos**; solo se declaran con medición en `validation.md`. Render gratis y Spark no tienen SLA: la disponibilidad se documenta como límite.
- Español es-CL, zona `America/Santiago`; áreas táctiles de 48 px o más, texto base 16 y estados con texto e ícono.

## Compatibilidad

- **Edge:** contrato idéntico; solo cambia `--server` (o `VIGIA_SERVER`) y el token se emite de nuevo.
- **App instalada:** la versión Django no funciona con el nuevo backend; se reinstala (piloto sin usuarios reales).
- **Django:** sigue en `develop` y en `web/` de esta rama hasta la autorización de fusión.
- Specs relacionadas: 010, 011, 012, 013, 014, 017 (reglas que se portan) y 015 (iOS).

## Supuestos y decisiones pendientes

- P-019-01 — **Herramientas locales:** resuelta con D-099 (instalación con `winget` autorizada).
- P-019-02 — **Revisión de reglas del backend base (D-087):** las diferencias 4 y 5 del plan (purga, exportación y eliminación) se resolvieron con D-098: se portan (RF-019-24..27). Las diferencias 1, 2, 3, 6 y 7 se aplican con su valor por defecto mientras el propietario no indique otra cosa.
- P-019-03 — **Cuentas externas:** pendiente por decisión del propietario (D-100). Proyecto Firebase real, Render y cron-job.org los crea el propietario más adelante. El punto de control (RF-019-22) necesita al menos el proyecto Firebase, porque los emuladores no entregan push a un teléfono.
- Supuesto técnico reversible: un solo proceso del backend en Render (la caché en memoria de RF-019-11 depende de eso).

## Revisión y cambios

- 2026-10-28: creada con las decisiones D-081..D-097 tras revisar `vigia 26`. Aprobación e implementación autorizadas en la misma sesión.
- 2026-10-28: «1. autorizo a instalarlos con winget, 2. las privacidad sobre todo, y 3. deja pendiente el crear el proyecto firebase, el servicio en Render y la tarea en cron-job.org. puedes seguir con T-019-04 si lo demas esta listo». Se agregan RF-019-24..27 (D-098), D-099 y D-100.
