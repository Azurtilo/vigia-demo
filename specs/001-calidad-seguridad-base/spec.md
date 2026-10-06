# 001 — CalidadBase

Estado: implementado y verificado técnicamente. Fecha: 2026-09-20.
Tipo: cambio transversal de seguridad, pruebas y configuración; no es una app Django.
Fuente: solicitud del propietario «CalidadBase», fase DOCUMENTAR.
Implementación autorizada: **SÍ**, mensaje del propietario del 2026-09-20. Aceptación funcional final: pendiente.

## Problema y resultado

La base tiene controles de registro y permisos, pero carece de pruebas reales y de una configuración aislada para ejecutarlas. El enlace Registro repite parcialmente la política del servidor y omite al superusuario sin perfil/cargo. Tailwind no escanea las clases completas presentes en Python y JavaScript propios.

El resultado esperado es poder verificar esos comportamientos con datos ficticios sin depender del entorno normal, hacer coherente el menú con el acceso directo y ampliar el escaneo sin incluir dependencias ni archivos generados.

## Estado previo comprobado

Inspección estática, no ejecución funcional, del 2026-09-20:

| Cambio manual informado | Evidencia actual | Tratamiento |
|---|---|---|
| requirements.txt convertido a UTF-8 | Decodificación UTF-8 estricta válida; 891 bytes, sin BOM ni bytes nulos | Ya aplicado; no recodificar ni cambiar versiones |
| media/ agregado a .gitignore | Regla presente; git check-ignore reconoce una ruta ficticia bajo media/ | Ya aplicado; conservar. media/profile.webp sigue versionado: ignorar no retira archivos ya rastreados |
| ACCOUNT_ADAPTER conectado | Originalmente estaba en core/settings.py; tras implementar quedó compartido en core/common_settings.py y resuelve UsuarioApp.adapters.NoSignupAccountAdapter | Conservado y probado por adapter y HTTP |
| ACCOUNT_ALLOW_REGISTRATION = True eliminado | ACCOUNT_ALLOW_REGISTRATION no aparece en core/settings.py | Ya aplicado; no restablecerlo |

Git estaba limpio en main, HEAD 2f2d1e6. Esto acredita el estado inspeccionado, no la historia de la conversión anterior. No se leyó .env, bases reales ni archivos personales. Estos ajustes no son tareas futuras.

## Alcance y exclusiones

Incluye configuración aislada, pruebas significativas de registro/usuarios/permisos, coherencia del enlace Registro, escaneo HTML/JS/Python y documentación de decisiones opcionales.

Excluye nuevas apps, modelos, endpoints, migraciones de esquema, actualización de dependencias, SMTP, verificación obligatoria de correo, activación o eliminación de axes/preventconcurrentlogins, cambios del gráfico demostrativo, rediseño de autenticación/MFA y cambios de permisos del listado o perfil. No incluye despliegue, commit ni push.

## Actores y permisos por acción

Todos los permisos positivos requieren autenticación y actividad. La excepción del superusuario tiene prioridad sobre perfil/cargo; un superusuario inactivo no obtiene acceso.

| Actor | GET /registro/ | POST /registro/ válido | Enlace Registro | Crear por /accounts/signup/ |
|---|---|---|---|---|
| Anónimo | No; redirigir al login | No; sin altas | No | No |
| Activo RESTRICTED | No; redirigir a Home | No; sin altas | No | No |
| Activo sin perfil, no superusuario | No; redirigir a Home | No; sin altas | No | No |
| Activo con perfil sin cargo, no superusuario | No; redirigir a Home | No; sin altas | No | No |
| Activo ADMIN | Sí | Sí | Sí | No |
| Activo MANAGER | Sí | Sí | Sí | No |
| Superusuario activo, incluso sin perfil o cargo | Sí | Sí | Sí | No |
| Inactivo, incluido superusuario | No | No; sin altas | No | No |

Con los backends actuales, un inactivo puede ser tratado como anónimo al recuperar la sesión: se acepta redirección al login en ese caso. Si la vista recibe un usuario autenticado inactivo, el helper lo rechaza y el mixin lo redirige a Home. No exigir que force_login convierta al inactivo en usuario autenticado efectivo. is_staff por sí solo no concede permiso.

## Historias y flujo

1. Un visitante intenta el registro público mediante GET o POST: ve el cierre correspondiente o la respuesta de allauth aplicable; nunca crea usuario, perfil ni dirección allauth.
2. ADMIN, MANAGER o superusuario activo ven Registro en la navegación compartida, abren el formulario y envían datos válidos. Se crean usuario y perfil asociado y se redirige a Register con el mensaje existente.
3. Un actor no autorizado intenta la URL directamente, incluso por POST: no hay altas. Ocultar el enlace no sustituye ese control.
4. Un operador autorizado envía datos inválidos: el formulario conserva errores y no crea registros. Un desarrollador verifica estos casos en un entorno de pruebas independiente.

## Requisitos

- **RF-001-01 — Aislamiento.** Ejecutar pruebas con core.test_settings sin leer .env ni requerir secretos, DB, correo, caché o media del entorno normal. Usar SQLite efímero, correo en memoria, hasher rápido exclusivo de pruebas, hosts de prueba y HTTPS/cookies seguras/HSTS desactivados solo allí. No activar esta configuración en producción.
- **RF-001-02 — Registro público cerrado.** Mantener conectado el adapter existente y probar su resolución efectiva y el cierre de GET/POST de /accounts/signup/, incluyendo ausencia de altas ante POST válido.
- **RF-001-03 — Autorización interna.** Proteger GET y POST de /registro/ según toda la matriz anterior; la denegación no crea cuentas ni perfiles. Conservar usuario_tiene_cargo como política y comprobar la excepción de superusuario y la precedencia de inactivo.
- **RF-001-04 — Formulario y alta.** Probar mediante el registro interno los campos obligatorios, username duplicado, correo con formato inválido si se informa, contraseñas inválidas/no coincidentes y cargo inválido. Un alta válida crea exactamente un User y un Profile vinculado al cargo elegido, con contraseña utilizable y sin privilegios staff/superusuario añadidos por el formulario.
- **RF-001-05 — Menú coherente.** El enlace Registro usa la misma autorización que la vista, sin comparar cargos en diferentes plantillas. Es visible para los actores permitidos y ausente para los denegados, en escritorio y móvil; verificar el href de Register en HTML además del acceso directo.
- **RF-001-06 — Compilación y escaneo Tailwind.** Usar Tailwind 4.3.0 mediante el binario standalone de django-tailwind 4.5.0, sin Node.js/npm. Conservar HTML y detectar clases completas en JavaScript y Python propios mediante fuentes CSS explícitas; excluir migraciones, staticfiles, dependencias y generados. Las clases concatenadas como "bg-" + color requieren un mapa con nombres completos o `@source inline()` finito. Validar compilación y presencia/ausencia de clases representativas.
- **RF-001-07 — Compatibilidad y decisiones opcionales.** Conservar los cuatro ajustes manuales, dependencias opcionales instaladas/declaradas y desactivadas, correo de consola con verificación none y gráfico de ejemplo. Documentar decisiones por proyecto y comprobar regresiones pertinentes sin convertir el inicio en dashboard real.

## Datos y reglas existentes

No hay datos nuevos ni cambios de esquema. User es el modelo de Django; Profile.user_FK es uno a uno; position_FK admite nulo en el modelo, pero ProfileCreateForm exige seleccionar un cargo. Position.user_position es único (45 caracteres); permission_code tiene ADMIN, MANAGER y RESTRICTED. El formulario actual excluye Position con pk=1: conservarlo y construir datos ficticios que hagan explícita esa condición, sin suponer que pk=1 representa siempre ADMIN.

UserCreateForm recibe username, email, first_name, last_name, password1 y password2. Probar username obligatorio/duplicado, validadores de contraseña actuales y formato de email informado. **No se establece una nueva unicidad u obligatoriedad del email interno:** ACCOUNT_UNIQUE_EMAIL y ACCOUNT_EMAIL_REQUIRED pertenecen a allauth, y el formulario interno no incorpora esa validación expresamente. La duplicidad mínima exigida aquí es username; endurecer correo interno requiere una decisión de alcance separada.

La imagen es opcional al crear; conservar el predeterminado profile.webp, rechazo de carga inválida o mayor que 5 MiB y procesamiento existente. Los archivos de prueba deben ser sintéticos y temporales. No introducir reglas de auditoría, retención o negocio ajenas al pedido.

## Criterios de aceptación

| RF | Dado / cuando | Entonces |
|---|---|---|
| RF-001-01 | Proceso de pruebas sin .env ni variables sensibles | Arranca con valores de prueba explícitos; no importa la configuración normal ni contacta servicios reales |
| RF-001-01 | Alta con imagen sintética y ejercicio de correo | DB en memoria, archivo solo en directorio temporal limpiado y correo solo en outbox; no usa media real |
| RF-001-02 | Resolver el adapter sin sustituir ACCOUNT_ADAPTER en tests | Se obtiene NoSignupAccountAdapter; is_open_for_signup devuelve False |
| RF-001-02 | GET y POST público, con payload que sería válido si el registro estuviera abierto | Registro cerrado; sin incremento de User, Profile ni EmailAddress |
| RF-001-03 | Cada actor de la matriz solicita GET/POST directo | Permisos y redirecciones acordes; toda denegación deja los conteos de altas intactos |
| RF-001-04 | ADMIN, MANAGER y superusuario envían datos válidos, por separado | Un usuario y su perfil, vínculo/cargo correctos, contraseña verificable, redirección y mensaje de éxito |
| RF-001-04 | Datos inválidos/duplicados o cargo omitido/inexistente/excluido | Errores del formulario pertinente, sin altas parciales por validación |
| RF-001-05 | Renderizar menú para cada actor y navegar en escritorio/móvil | Presencia o ausencia de enlace por política; superusuario sin perfil/cargo lo ve y puede usarlo |
| RF-001-06 | `python manage.py tailwind build` en un entorno reproducible desde `requirements.txt` | Compila con Tailwind 4.3.0 sin Node.js; CSS contiene clases de fuentes propias HTML/JS/Python y no depende de migraciones/generados |
| RF-001-07 | Comparar configuración y flujos tras la implementación | Opcionales desactivados, consola/none, login/MFA y gráfico demostrativo preservados; cambios manuales conservados |

## No funcionales y compatibilidad

Sin consulta a datos reales. La actualización de `django-tailwind` y su dependencia `pytailwindcss` queda limitada a reemplazar el flujo npm de Tailwind; no agrega una dependencia de Node.js. Conservar es-cl, America/Santiago, CBV, rutas y nombres actuales, bloques y componentes compartidos. Tailwind 4 requiere navegadores modernos; mantener navegación por teclado y móvil dentro de esa compatibilidad. No cambiar la política del resto de las vistas por generalizar los permisos de Registro. Una suite con cero casos no satisface esta especificación.

## Supuestos, límites y revisión

No hay decisiones críticas ausentes para documentar. Las elecciones técnicas del [plan](plan.md) son propuestas para revisión, no acuerdos ya aprobados. El guardado actual de User y Profile es secuencial sin transacción explícita; este alcance prueba alta válida y rechazo antes de guardar, no promete atomicidad ante fallo de almacenamiento/DB. Una ampliación de esa garantía se documentará por separado.

2026-09-20: primera versión documental solicitada; el propietario la revisó, aprobó y autorizó todas las tareas. Implementación y evidencia técnica terminadas en [validation.md](validation.md); aceptación funcional final pendiente.

2026-09-22: el propietario autorizó documentar, implementar y verificar la migración ya iniciada a Tailwind 4 sin Node.js, la revisión de `ROADMAP.md`/`VERIFICACION.md` y el detalle de pruebas por RF. RF-001-06 sustituye para esta base la elección previa de Tailwind 3/npm; no cambia permisos, datos ni UI funcional deliberadamente. Evidencia en [validation.md](validation.md#ajuste-del-2026-09-22).

## Sustitución acotada por spec 006 — 2026-10-02

Los RF y decisiones originales se conservan como historial. La política de Registro que admitía root sin cargo y excluía Position.pk=1 quedó sustituida únicamente en esa acción por RF-006-01/02, confirmados/autorizados posteriormente: cargo obligatorio; ADMIN registra inferiores, MANAGER RESTRICTED, solo root con ADMIN registra ADMIN. Core.mixins conserva su helper para otras acciones; menú/Registro comparten ahora cargos_asignables. 006 corrige atomicidad/fotos sin reescribir la evidencia histórica de 001. Dependencias actuales corresponden a 005.

## Evolución autorizada por spec 007 — 2026-10-06

En este derivado, el propietario solicita registro público local/Google con altas RESTRICTED y verificación antes de contratar. [007-PlanesApp](../007-planes-app/spec.md) propone sustituir RF-001-02 (cierre público) y ampliar privacidad de Home/listado y correo de RF-001-07. **Implementado tras autorización posterior del alcance completo**: esta spec y su evidencia de cierre se conservan como historial. [Validación 007](../007-planes-app/validation.md). Políticas de Registro/gestión 004/006 no se sustituyen; los tests del cierre/lectura se adaptaron trazablemente en 007 y la suite completa pasó.
