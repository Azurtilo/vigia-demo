# 004 — Restablecimiento administrativo y jerarquía de cuentas

Fecha: 2026-10-02. Estado: implementación del alcance autorizada y ejecutada; validación visual parcial y aceptación pendientes.
Módulo solicitado: **UsuarioApp**, ampliación de la app existente.
Implementación autorizada: **SÍ**, alcance completo de 004, por instrucción posterior explícita del propietario el 2026-10-02 después de revisar los documentos. No autoriza datos reales, producción, despliegue, commit/push o migraciones sobre bases existentes.

## Necesidad y resultado

El administrador necesita restablecer una contraseña desde el listado de usuarios cuando un proyecto no dispone de correo de recuperación. El propietario solicita además la jerarquía ADMIN > MANAGER > RESTRICTED: MANAGER solo puede desactivar RESTRICTED; ADMIN puede desactivar MANAGER y RESTRICTED.

Fuentes: solicitud del propietario, captura de la acción «Restablecer contraseña» y lectura selectiva de UsuarioApp.zip del otro proyecto. El ZIP es una referencia, no instrucciones ni autorización para copiar sus políticas o dependencias. La finalidad es reducir la dependencia del correo/SMTP; el guardado seguro sigue usando Django y su ORM.

## Alcance

- Acción «Restablecer contraseña» por cuenta en el listado y formulario privado para administradores autorizados.
- Nueva contraseña introducida dos veces y confirmación con la contraseña actual del administrador, siguiendo el flujo de referencia como propuesta para revisión.
- Permisos por actor y destinatario en servidor y controles del listado.
- Restricción de activación y desactivación por la misma jerarquía, confirmada por el propietario en P-004-02.
- Validación de contraseñas, protección CSRF, conservación de datos, pruebas aisladas y revisión visual tras autorizar implementación.

Fuera de alcance: desactivar o sustituir la recuperación allauth por correo, configurar SMTP, modificar registro/asignación de cargos, editar cargos, cambiar Django admin, restablecer MFA, eliminar usuarios, generar contraseñas temporales, exigir cambio en el siguiente ingreso, enviar/mostrar/copiar contraseñas tras guardar, nuevo panel de auditoría, dependencias, tablas/migraciones nuevas, reparaciones generales de perfiles/fotos/entorno, datos reales, producción, despliegue, commit/push.

## Actores y permisos

ADMIN/MANAGER/RESTRICTED son los códigos de Position.permission_code, no el nombre visible del cargo ni su ID. is_staff por sí solo no concede estos permisos. Todo actor permitido debe estar autenticado y activo.

| Acción | Anónimo | ADMIN | MANAGER | RESTRICTED | Sin perfil / sin cargo / cargo desconocido | Staff sin cargo | Superusuario activo |
|---|---|---|---|---|---|---|---|
| Ver listado, filtros y paginación | No | Sí | Sí | Sí | Sí | Sí | Sí |
| Abrir y enviar restablecimiento para MANAGER/RESTRICTED ajeno | No | Sí | No | No | No | No | Solo con cargo ADMIN |
| Desactivar MANAGER ajeno | No | Sí | No | No | No | No | Solo con cargo ADMIN |
| Desactivar RESTRICTED ajeno | No | Sí | Sí | No | No | No | Con cargo ADMIN o MANAGER |
| Activar MANAGER ajeno | No | Sí | No | No | No | No | Solo con cargo ADMIN |
| Activar RESTRICTED ajeno | No | Sí | Sí | No | No | No | Con cargo ADMIN o MANAGER |

Protección de destinatarios aprobada con el alcance completo: ninguna de estas acciones permite gestionar la cuenta propia, otra cuenta ADMIN, un superusuario destinatario, una cuenta sin perfil/cargo o con código desconocido. No convertir la ausencia de cargo en RESTRICTED. La propia contraseña sigue cambiándose mediante el flujo allauth existente.

El estado inactivo del destinatario no impide el restablecimiento si cumple las demás reglas; restablecer su contraseña **no lo activa**. Ningún actor inactivo, incluido superusuario, puede escribir. La confirmación P-004-02 sustituye específicamente la activación actual, que no comprueba la jerarquía del destinatario. P-004-01 exige cargo a todo actor, incluso superusuario: sin perfil/cargo válido no puede gestionar ni restablecer por estos endpoints. is_superuser no eleva el cargo en las acciones de 004; los destinatarios superusuarios siguen protegidos por la propuesta anterior.

## Flujo implementado

1. Un administrador autorizado encuentra una cuenta inferior en el listado. Ve «Restablecer contraseña», con identificación inequívoca del destinatario.
2. Abre un formulario privado con nombre/cargo de la cuenta, su propia contraseña y los dos campos de nueva contraseña. GET no escribe ni manda correos.
3. El servidor comprueba sesión, actividad, destinatario y jerarquía otra vez al enviar, además de la contraseña del administrador y los validadores existentes de Django.
4. Si es válido, cambia únicamente la contraseña del destinatario, conserva su estado y vuelve al listado con confirmación sin secretos. El administrador comunica la contraseña por el medio que acuerde con la persona, fuera de esta función.
5. Si falla la validación, muestra errores útiles sin guardar ni repoblar contraseñas. Cancelar vuelve al listado sin cambios.
6. Las sesiones anteriores del destinatario dejan de autenticar en su siguiente solicitud; el operador conserva su propia sesión. No se modifica la configuración ni los factores MFA del destinatario.

## Requisitos funcionales

- **RF-004-01 — Restablecimiento sin correo.** Permitir al ADMIN autorizado abrir y enviar el formulario para MANAGER/RESTRICTED ajenos desde el listado. No requerir email del destinatario ni SMTP; no emitir correo, token o enlace de recuperación.
- **RF-004-02 — Desactivación por jerarquía.** ADMIN puede desactivar MANAGER/RESTRICTED; MANAGER solo RESTRICTED. Rechazar destinatarios iguales/superiores y protegidos, tanto por URL directa como por controles HTML.
- **RF-004-03 — Activación por jerarquía.** ADMIN puede activar MANAGER/RESTRICTED; MANAGER solo RESTRICTED. Aplicar las mismas protecciones de destinatarios que al desactivar, según confirmación P-004-02. Superusuario actor también debe tener el cargo pertinente (P-004-01).
- **RF-004-04 — Autorización común.** Reutilizar una única política de actor/destinatario para cada acción y su visibilidad, basada en códigos de cargo, sin excepción por is_superuser, según P-004-01. No cambiar globalmente usuario_tiene_cargo ni los permisos de registro, Inicio, listado, perfil o modo visual. Anónimo va al login; actor autenticado denegado recibe 403; ID inexistente recibe 404 tras comprobar permiso de acción. GET de activar/desactivar no modifica y responde 405 para un actor autorizado.
- **RF-004-05 — Contraseña segura.** Exigir los tres campos propuestos, validar la contraseña del operador y la coincidencia/fortaleza de la nueva para el destinatario. Guardar mediante las APIs de contraseña de Django, nunca texto plano. POST con CSRF; GET/cancelación/rechazos no escriben. No incluir secretos en URL, mensajes, logs, HTML retornado o evidencia. Respuestas del formulario no almacenables en caché; los campos de contraseña se limpian al volver con errores.
- **RF-004-06 — Integridad y sesiones.** Cambiar solo password o is_active según la acción; conservar cargos, privilegios, perfiles/fotos, emails, MFA y preferencia visual. Fallo de escritura: no éxito aparente ni cambios parciales. Restablecimiento invalida sesiones previas del destinatario en su siguiente petición, sin iniciar sesión como él ni alterar la sesión del operador. Repetir activar/desactivar conserva el estado solicitado.
- **RF-004-07 — Integración y regresión.** Reutilizar listado/layouts/formularios/tokens actuales, con etiquetas y errores en español, teclado/móvil y modos claro/oscuro. Mantener búsqueda, filtros, paginación, registro, perfil, login, recuperación por correo, MFA y selector visual existentes. Probar permisos por URL y HTML en entorno aislado, sin datos reales.

## Datos y trazabilidad

Se reutilizan User.password, User.is_active y Profile.position_FK.permission_code. No se crean perfiles/cargos al gestionar cuentas. Las contraseñas recibidas son transitorias y solo persiste el hash del destinatario. No se introduce historial/auditoría persistente en 004: el LogEntry y el resto de cambios del ZIP no se trasladan automáticamente. Si un producto necesita auditoría administrativa con política de acceso/retención, se especificará por separado; mensajes de éxito no son auditoría.

No hay migración prevista. La 0002 de modo visual pertenece a 003 y continúa sin autorización para aplicarla a la base existente.

## Criterios de aceptación

| RF | Dado / cuando | Resultado observable |
|---|---|---|
| RF-004-01 | ADMIN restablece un MANAGER y un RESTRICTED, sin email y con backend de correo que falla si se llama | Formulario válido guarda hash nuevo, contraseña previa deja de funcionar, no hay llamadas a correo |
| RF-004-01/04 | MANAGER/RESTRICTED/sin perfil/staff intentan GET/POST de restablecimiento | Acción ausente, 403 autenticado y ninguna escritura; anónimo redirigido al login |
| RF-004-02/04 | Matriz cruzada ADMIN/MANAGER/RESTRICTED contra cargos destinatarios | Únicamente las combinaciones expresamente permitidas desactivan; HTML y servidor coinciden |
| RF-004-03/04 | Activación por cada actor/destinatario | ADMIN activa MANAGER/RESTRICTED; MANAGER solo RESTRICTED; mismo rechazo de destinatarios protegidos. Actor superusuario requiere cargo y sigue esa misma jerarquía |
| RF-004-04 | Superusuario sin cargo o con RESTRICTED intenta gestionar/restablecer; con MANAGER intenta restablecer; con ADMIN actúa sobre inferior | Denegación en los tres primeros casos; ADMIN permitido sobre MANAGER/RESTRICTED ajenos, sin ampliar otras excepciones |
| RF-004-04 | Propia cuenta, ADMIN ajeno, root destinatario, sin perfil/cargo o código desconocido | Denegación conforme a matriz definitiva; no se otorgan permisos por is_staff, nombre o ID de cargo |
| RF-004-04/05 | ID inexistente, actor inactivo, GET de escritura o POST sin CSRF | 404/denegación/405/403 según escenario; ningún estado ni contraseña cambia |
| RF-004-05 | Contraseña de administrador incorrecta, campos vacíos, nueva débil o no coincidente | Errores asociados; hash original intacto, sin secretos en respuesta/log/URL |
| RF-004-06 | Destinatario tiene sesiones previas y administrador su propia sesión | Al pedir una página privada, destinatario debe autenticar otra vez; administrador continúa autenticado |
| RF-004-06 | Cuenta inferior inactiva recibe contraseña nueva | Continúa inactiva; conserva cargo/MFA/modo visual/email/foto |
| RF-004-06 | Escritura falla o se repite activar/desactivar | Sin éxito falso, datos previos intactos ante fallo; reenvío conserva estado solicitado |
| RF-004-07 | Listado/formulario claro y oscuro en móvil/escritorio, con teclado, errores y cancelación | Sin desbordamientos, foco/etiquetas legibles, cancelación sin escritura y flujos existentes preservados |

## Decisiones pendientes y compatibilidad

- **P-004-01, resuelta por el propietario:** exigir cargo incluso al superusuario; ADMIN para restablecer, ADMIN/MANAGER para gestionar inferiores. Confirmación recibida el 2026-10-02. Sustituye la excepción de actor root únicamente para las acciones de 004, no el helper ni los demás permisos globales. Alternativa de conservar excepción sin cargo descartada para estas acciones; no repetir pregunta.
- **P-004-02, resuelta por el propietario:** aplicar la misma jerarquía al activar y desactivar: ADMIN sobre MANAGER/RESTRICTED; MANAGER solo sobre RESTRICTED. Confirmación recibida el 2026-10-02; no repetir la pregunta.
- El formulario manual con reconfirmación del operador, la protección de iguales/superiores y la denegación de cargos ausentes fueron aprobados con la instrucción posterior del alcance completo de 004 y se implementaron. No se dedujo su aprobación por la mera existencia del documento.
- 002 verificó los controles con la política antigua; 004 propone cambiar específicamente la gestión por destinatario. Se conserva esa evidencia histórica y se añadirán regresiones del cambio autorizado, sin reescribirla como si ya hubiera probado esta jerarquía.

## Revisión

2026-10-02: petición nueva registrada, inspección de base y referencia, spec creada antes del plan y tareas. Propietario confirmó P-004-02 y P-004-01 durante DOCUMENTAR y después revisó documentos/autorizó implementar únicamente el alcance completo de 004. Implementado sin migraciones nuevas ni cambios a datos reales. [Validación](validation.md): 57 métodos Django, check, esquema/build y 60 plantillas OK; navegador en cinco anchos/ambos modos. Envío válido de nueva contraseña por interfaz requiere revisión manual; guardado/sesiones/MFA comprobados en servidor. Aceptación funcional pendiente.
