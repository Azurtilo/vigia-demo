# Plan técnico — 001 / CalidadBase

Spec: [spec.md](spec.md). Fecha: 2026-09-20.
Estado: implementado según propuesta y verificado. Autorización concedida el 2026-09-20.

## Inspección y nombre

Se leyeron las instrucciones, constitución, README, documentos de proyecto/estado/arquitectura/observaciones/decisiones/trazabilidad/entorno, guías 01–03 y plantillas SDD. Se contrastaron core/settings.py, core/mixins.py, rutas raíz y de apps, adapters/forms/models/views/tests/apps/choices y migración inicial de UsuarioApp, homeApp/views.py/middleware.py/tests.py, utilidades de imagen, plantillas de registro/inicio/navegación/layout, JavaScript del gráfico, requirements, gitignore y configuración/package de Tailwind.

El índice y el directorio specs solo contenían README.md y _templates; 001 y 001-calidad-seguridad-base estaban libres. Se conserva **CalidadBase** como nombre del cambio y la carpeta sugerida por el usuario; no requiere nombre de paquete, startapp, LOCAL_APPS ni include nuevos.

Git limpio al inicio en main, HEAD 2f2d1e6. Los cuatro ajustes manuales están aplicados según [spec](spec.md). También se preservan las mejoras existentes de actividad y avatar. El atributo real del mixin es **permisos**, no permisos_docente como decía AGENTS.md; la corrección es documental, sin renombrar código.

## Diseño propuesto

### 1. Separar configuración común de las entradas de entorno

No basta con importar core.settings y sobrescribir DATABASES después: ese módulo lee .env y exige SECRET_KEY durante la importación. Se propone una extracción acotada, sin reestructurar todo el proyecto:

- **Nuevo core/common_settings.py:** configuración compartida que no lee entorno ni abre recursos: BASE_DIR, rutas de plantillas, listas de apps, middleware, backends, validadores, adapter allauth, MFA, idioma, zona y opciones comunes. Mantener los comentarios de capacidades opcionales junto a las listas donde corresponden.
- **Existente core/settings.py:** sigue siendo la entrada normal de manage.py, WSGI y ASGI. Importa lo común y conserva carga de .env, clave requerida, valores/configurabilidad de DEBUG, hosts, orígenes CSRF, HTTPS, cookies, HSTS, INTERNAL_IPS, DB normal, media, hashers, correo de consola y logging. No cambiar sus defaults efectivos ni las opciones de despliegue.
- **Nuevo core/test_settings.py:** importa solo common_settings y define todos los recursos de prueba. Nunca importa settings, llama a read_env, modifica os.environ ni usa fallback a secretos normales. El adapter y la política de correo allauth se comparten, no se simulan con overrides para hacer pasar pruebas.

Se elegirá qué constantes quedan en common_settings mediante inventario exhaustivo antes de moverlas. ACCOUNT_ADAPTER puede trasladarse literalmente allí: el ajuste manual se conserva efectivo en la configuración normal, sin duplicarlo ni revertirlo. La localización actual sigue siendo core/settings.py hasta implementar. No crear mecanismos automáticos que detecten tests por argv ni cambien producción accidentalmente.

| Configuración de pruebas propuesta | Valor / control |
|---|---|
| SECRET_KEY y DEBUG | Clave fija inequívocamente ficticia y DEBUG False; ningún secreto externo |
| DATABASES.default | django.db.backends.sqlite3; NAME y TEST.NAME en memoria; sin alias apuntando a db.sqlite3 |
| EMAIL_BACKEND | django.core.mail.backends.locmem.EmailBackend; validar outbox mediante un envío sintético |
| PASSWORD_HASHERS | Solo MD5PasswordHasher en pruebas; conservar AUTH_PASSWORD_VALIDATORS comunes |
| Seguridad HTTP de pruebas | SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE False; SECURE_HSTS_SECONDS 0, INCLUDE_SUBDOMAINS y PRELOAD False; SECURE_PROXY_SSL_HEADER None |
| Hosts y orígenes | ALLOWED_HOSTS testserver, localhost, 127.0.0.1 y [::1]; CSRF_TRUSTED_ORIGINS vacío |
| Archivos | MEDIA_ROOT y STATIC_ROOT en TemporaryDirectory exclusivo del proceso, con limpieza; FileSystemStorage local para soportar image.path; subdirectorio temporal por caso que cargue imágenes y limpieza con addCleanup |
| Caché | LocMemCache con ubicación de pruebas y limpieza entre escenarios que dependan de limitadores allauth |
| Sesiones y logs | Sesiones en DB efímera; logs solo consola; sin handlers de archivos ni red |

El directorio temporal global necesita conservar su objeto y registrar cierre al finalizar el proceso; los casos que escriben archivos añaden limpieza incluso si fallan. No copiar media/profile.webp real: generar una imagen sintética si un caso necesita el predeterminado. Evitar InMemoryStorage aquí porque Profile.save y customer_img usan rutas locales y PIL. Estas rutas temporales son recursos de prueba, nunca rutas de producción.

Validar antes de la suite la importación en un proceso con entorno mínimo y sin .env; instrumentar la lectura de .env para que falle si se intenta. Comparar la configuración normal antes/después con entorno **sintético** y carga de .env bloqueada, incluyendo seguridad, adapter, apps, middleware, email y rutas. No imprimir valores del entorno real. WSGI/ASGI/manage.py siguen apuntando a core.settings; --settings=core.test_settings es explícito en los comandos de prueba.

Alternativas descartadas: copiar toda la configuración en test_settings genera divergencia de permisos/allauth; importar settings y luego sobrescribir lee primero configuración sensible; añadir parches de entorno en el módulo de pruebas oculta dependencias y efectos globales. La extracción propuesta permite reutilizar la configuración relevante sin esas dependencias y exige comprobar equivalencia del entorno normal.

### 2. Una fuente de autorización para vista y navegación

Elegir **context processor core/context_processors.py** (nuevo), con una variable booleana de acción, propuesta como puede_registrar_usuarios. Calcula el resultado mediante usuario_tiene_cargo y los cargos configurados en PermitsPositionMixin.permisos; no repite las cadenas ADMIN/MANAGER ni añade privilegios por is_staff. UserCreateView hereda actualmente ese atributo sin sobrescribirlo. Una prueba de integración de la matriz detectará futuros desacuerdos si se personaliza esa vista.

Registrar el processor en TEMPLATES dentro de la configuración compartida y sustituir solo la condición del enlace Registro en templates/components/navbar/nav.html. El servidor conserva su mixin y helper. Reutilizar navbar_desktop y navbar_mobil, que incluyen el mismo nav, y los layouts base_extendido.html/base_pages.html.

Se prefiere un processor porque la autorización de la navegación común se necesita en las páginas internas ya renderizadas con request; evita repetir la llamada y cargar tags en ambos contenedores. Un template tag sería válido, pero añade registro/carga y cálculo por inclusión sin ventaja para este único booleano. No añadir una app ni una capa genérica de autorización. Comprobar que anónimos y usuarios sin perfil no producen excepciones.

### 3. Pruebas propias de la base

Extender UsuarioApp/tests.py y homeApp/tests.py existentes, hoy sin casos. Mantener clases separadas por configuración, registro público, permisos, formulario y navegación dentro de esos archivos mientras el tamaño sea manejable. No añadir pytest ni una infraestructura paralela.

Crear usuarios, perfiles y cargos ficticios explícitamente: la migración inicial no siembra cargos, y el formulario excluye pk=1. Reservar ese registro para el caso excluido y usar cargos elegibles distintos en altas válidas; nunca depender de datos de desarrollo ni equiparar cargo a PK. Para actores sin perfil, no crear el perfil incidentalmente al visitar /perfil/.

### 4. Compilación y escaneo Tailwind

La implementación inicial conservó Tailwind 3, npm y los plugins existentes en `theme/static_src/tailwind.config.js`. Esa elección fue sustituida el 2026-09-22 por Tailwind 4.3.0 standalone: `django-tailwind==4.5.0` administra el binario mediante `pytailwindcss`, y `core/common_settings.py` fija explícitamente modo y versión. Se eliminan `package.json`, lockfile, PostCSS y configuración JavaScript; no se requiere Node.js.

Tailwind 4 usa configuración CSS-first. `theme/static_src/src/styles.css` importa Tailwind con detección automática desactivada y registra con `@source` las raíces propias de plantillas, JavaScript y Python. Se excluyen migraciones, cachés y `staticfiles`; una app futura debe añadir su raíz. Un `tailwind.config.js` legado solo sería leído mediante `@config` y no es necesario en esta base.

Las clases de `ProfileCreateForm` justifican escanear Python. Para clases dinámicas, preferir mapas de valores con utilidades completas o `@source inline()` finito. No agregar listas masivas ni concatenaciones que Tailwind no pueda detectar. La verificación debe compilar desde las dependencias declaradas, confirmar el encabezado de versión y revisar clases representativas. Si se prueban testigos temporales de inclusión/exclusión, retirarlos y recompilar antes de entregar.

## Mapa de archivos y requisitos

| RF | Existentes a modificar en futura implementación | Nuevos propuestos | Evidencia prevista |
|---|---|---|---|
| RF-001-01 | core/settings.py, UsuarioApp/tests.py | core/common_settings.py, core/test_settings.py | Importación sin entorno normal, equivalencia normal con datos ficticios, DB/mail/media/cache aislados |
| RF-001-02 | UsuarioApp/tests.py; adapter actual conservado | Ninguno adicional | Adapter real y GET/POST signup sin altas |
| RF-001-03 | UsuarioApp/tests.py; core/mixins.py y vista conservados | Ninguno adicional | Matriz completa GET/POST y helper con inactivo |
| RF-001-04 | UsuarioApp/tests.py; forms/models/views conservados inicialmente | Ninguno adicional | Altas válidas, errores y conteos/vínculos |
| RF-001-05 | templates/components/navbar/nav.html, UsuarioApp/tests.py, homeApp/tests.py | core/context_processors.py; integración en common_settings propuesto | HTML y URL coherentes, navegador móvil/escritorio |
| RF-001-06 | theme/static_src/src/styles.css; core/common_settings.py; requirements.txt; CSS generado | `pytailwindcss` como dependencia de django-tailwind 4.5.0 | Instalación reproducible, build standalone y revisión de fuentes/inclusión |
| RF-001-07 | homeApp/tests.py y documentación relacionada | validation.md solo al validar | Regresiones, revisión del diff, evidencia de opcionales conservados |

Un defecto que aparezca al escribir pruebas debe reproducirse y corregirse dentro de los RF autorizados, con regresión pertinente. No editar spec para legitimar el defecto ni ampliar automáticamente el alcance a otras vistas. Cualquier archivo adicional se justifica y se refleja en tareas antes de intervenir.

## Datos, contratos, transacciones y migraciones

No hay modelos, endpoints, formularios públicos ni migraciones nuevos. Conservar Register en /registro/, Home en / y User en /usuarios/. El POST interno usa UserCreateForm y ProfileCreateForm y redirige a Register al tener éxito. El rechazo de validación debe dejar User/Profile intactos.

No se añade unicidad de email al formulario interno por inferirla de allauth. No se cambia la exclusión de pk=1 ni la política de asignación de cargos. El guardado secuencial no garantiza rollback ante fallo posterior de Profile o imagen; queda como límite conocido fuera de esta entrega, sin introducir transacciones o servicios por rutina.

Reversión futura: revertir conjuntamente extracción/importaciones de configuración; retirar processor y condición de menú en conjunto si fuera necesario; restaurar patrones Tailwind y recompilar. No tocar datos, migraciones, ajustes manuales ni archivos del usuario para revertir este cambio.

## Plan de pruebas y comprobaciones

Los IDs siguientes son escenarios previstos, **no tests existentes ni ejecutados**.

| ID / RF | Casos y aserciones pertinentes |
|---|---|
| P-01 / RF-001-01 | Importación sin .env/secretos; falla controlada si se intenta leer .env. Configuración normal con entradas sintéticas mantiene valores y mecanismos anteriores. DB en memoria desde la carga; envío ficticio aparece en outbox; archivo sintético queda en temporal y se limpia; hasher rápido solo en test_settings |
| P-02 / RF-001-02 | get_adapter con configuración compartida real devuelve NoSignupAccountAdapter y cierra registro. GET anónimo muestra signup_closed; POST válido no incrementa User/Profile/EmailAddress. Repetir intentos con actores autenticados para acreditar que ningún rol abre registro público. Determinar código HTTP concreto según allauth 0.62.1 instalado, sin aceptar un 500 o un bloqueo accidental por HTTPS/CSRF como evidencia de cierre |
| P-03 / RF-001-03 | GET y POST válidos para anónimo, RESTRICTED, sin perfil, sin cargo, ADMIN, MANAGER, superusuario sin perfil y con perfil sin cargo. Comprobar redirecciones login/Home y cero altas en denegados. is_staff sin cargo tampoco accede |
| P-04 / RF-001-03, RF-001-05 | Usuario inactivo de cargo permitido y superusuario inactivo: cliente/backends reales rechazan sesión; RequestFactory con usuario inactivo verifica además helper/mixin/processor, para no confundir recuperación de sesión con la política de actividad |
| P-05 / RF-001-04 | Alta independiente por ADMIN/MANAGER/superusuario: +1 User y +1 Profile, relación/cargo/datos correctos, check_password válido, is_staff/is_superuser False, redirección Register y mensaje de éxito. Imagen opcional funciona sin abrir el avatar real |
| P-06 / RF-001-04 | POST con username vacío/duplicado, email informado mal formado, contraseñas débiles o discordantes, cargo vacío/inexistente/pk=1, archivo no imagen o mayor que 5 MiB. Afirmar errores del formulario correspondiente y ningún User/Profile creado; no imponer email único sin decisión |
| P-07 / RF-001-05 | GET Home y Register cuando corresponde: analizar enlaces por href resuelto, no por cualquier texto «Registro». Matriz en nav renderizado para todos los actores; incluir anónimo/inactivo por render con RequestContext porque Home no les permite llegar al menú. Ambos contenedores heredan la misma decisión; no exigir un único enlace total si el DOM contiene escritorio y móvil |
| P-08 / RF-001-06 | `python manage.py tailwind build`; testigos exclusivos JS/Python incluidos y migración excluida. Retirar fuentes de prueba y recompilar para entregar CSS limpio; confirmar encabezado Tailwind 4.3.0 |
| P-09 / RF-001-07 | Login válido con credenciales ficticias y redirección; Home/listado accesibles por usuarios activos incluso RESTRICTED sin imponer nuevos cargos; páginas login/MFA conservan resolución/render según autenticación requerida. Home sigue con gráfico de ejemplo y tabla de accesos independiente; comparar defaults normales, dependencias y ajustes preservados |

Usar TestCase para pruebas con DB. Mantener middleware y backends comunes para comprobar integración real; usar RequestFactory solo para los casos de autorización que la sesión descarta antes de llegar a la vista. Añadir un caso de POST interno con comprobación CSRF real si se modifica la integración del formulario; no crear pruebas genéricas de Django sin vínculo al comportamiento local.

Después de crear la configuración y casos, comandos desde la raíz y en entorno virtual de desarrollo:

```bash
python manage.py check --settings=core.test_settings
python manage.py makemigrations --check --dry-run --settings=core.test_settings
python manage.py test UsuarioApp homeApp --settings=core.test_settings
```

La suite utiliza migraciones existentes solo para construir la DB efímera; no autoriza migrar la DB real. Comprobar conteo mayor que cero, casos por RF y resultados completos. No ejecutar la suite normal sin --settings mientras se exige aislamiento.

Para Tailwind 4 standalone:

```bash
python manage.py tailwind build
```

Navegador obligatorio al validar el menú: instancia local con datos ficticios y recursos aislados, escritorio y móvil, abrir/cerrar navegación móvil, seguir Registro, usar teclado, comprobar superusuario sin perfil y actores denegados. Preparar la instancia sobre DB temporal de archivo separada si se requiere persistir datos entre procesos; no usar db.sqlite3 ni convertir SQLite en memoria en servidor de validación multiproceso. No se planea crear esa instancia en DOCUMENTAR.

## Riesgos y dependencias

- La extracción de configuración debe conservar defaults y orden de importación. La comparación con entorno sintético y revisión del diff preceden la validación funcional.
- Profile.save procesa imágenes por ruta: aislar MEDIA_ROOT desde el inicio, incluyendo fixtures. No usar archivos reales como evidencia ni copiar el avatar del usuario.
- Paquetes declarados no equivalen a instalación local verificada. No se instalaron dependencias ni se ejecutó Django durante DOCUMENTAR; se comprobarán versiones disponibles al implementar, sin actualizarlas dentro de este alcance.
- No atribuir al formulario interno garantías exclusivas de allauth ni fijar un status HTTP no comprobado del signup cerrado.
- Las listas positivas de Tailwind requieren registrar raíces de futuras apps. Los controles excluidos deben probarse con utilidades que no aparezcan en otra fuente propia.
- axes y preventconcurrentlogins quedan opcionales y desactivados; correo real exige configuración y pruebas por proyecto; el gráfico conserva datos demostrativos y deberá sustituirse cuando un módulo futuro requiera métricas reales.

## Documentación y decisiones

Actualizar índice, proyecto, estado, observaciones, decisiones y trazabilidad según el estado real. No modificar constitution.md: no hay contradicción de principios.

No hubo decisiones críticas pendientes. Los comandos, resultados, navegador y límites reales quedaron registrados en [validation.md](validation.md).

Referencias técnicas consultadas el 2026-09-20: la [guía de pruebas Django 5.1](https://docs.djangoproject.com/en/5.1/topics/testing/overview/) describe el aislamiento de DB y advierte que otros recursos, como cachés, requieren atención; la [configuración de contenido de Tailwind 3](https://v3.tailwindcss.com/docs/content-configuration) fundamenta raíces explícitas, resolución relativa y nombres de clases completos/safelist. El diseño concreto anterior se deriva de inspeccionar esta base.

Actualización técnica del 2026-09-22: la [guía de actualización de Tailwind 4](https://tailwindcss.com/docs/upgrade-guide) establece que los archivos JavaScript ya no se detectan automáticamente, y la [documentación de fuentes](https://tailwindcss.com/docs/detecting-classes-in-source-files) define `@source`, exclusiones y safelist CSS. La [configuración de django-tailwind](https://django-tailwind.readthedocs.io/en/latest/settings.html) documenta el modo y versión del binario standalone.
