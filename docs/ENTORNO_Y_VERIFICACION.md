# Entorno y verificación

La base incluye documentación SDD y una configuración aislada para sus pruebas iniciales.

## Al desarrollar una copia nueva

Trabajar con entorno virtual propio y datos ficticios. La configuración carga .env en la raíz. SECRET_KEY es obligatoria; DEBUG, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS e INTERNAL_IPS son configurables. También lo son las opciones HTTPS del archivo settings.py.

No copiar el .env de un cliente. Una instalación local con HTTP necesita configuración local coherente con ese entorno; no trasladar esos ajustes al hosting. Tailwind usa un binario standalone descargado por `pytailwindcss`; Node.js y npm no forman parte del entorno requerido.

Instalación de dependencias declaradas, desde la raíz y dentro del entorno virtual:

```bash
python -m pip install -r requirements.txt
```

El archivo está en UTF-8 sin BOM. No sustituirlo por un pip freeze del entorno global.

Para levantar una base nueva, las migraciones y la creación de cuentas son pasos de instalación local separados de SDD. Ejecutarlos solo sobre la copia/base prevista; no inicializar o reemplazar una base existente como efecto de documentar.

## Comandos existentes

Con dependencias y configuración local preparadas:

```bash
python manage.py check --settings=core.test_settings
python manage.py makemigrations --check --dry-run --settings=core.test_settings
python manage.py test UsuarioApp homeApp --settings=core.test_settings
```

check no demuestra seguridad completa. makemigrations con estos parámetros detecta diferencias sin generar archivos. Verificar siempre el conteo real y los escenarios por RF.

`core.test_settings` no importa la entrada normal ni lee `.env`: usa SQLite en memoria, correo y caché locales, hasher rápido, seguridad HTTP desactivada para el cliente de pruebas y media/static root temporales. No ejecutar estas pruebas sin el argumento `--settings`.

Al añadir un módulo, ejecutar sus pruebas concretas y la regresión pertinente de los componentes compartidos. Registrar comandos y resultados reales, no solo una lista de comandos sugeridos.

## Tailwind

Desde la raíz, cuando una implementación cambie estilos, clases o fuentes:

```bash
python manage.py tailwind build
```

La versión standalone está fijada en `core/common_settings.py` y la compilación genera `theme/static/css/dist/styles.css`. No existen `package.json`, `package-lock.json` ni `tailwind.config.js`. El escaneo se configura en `theme/static_src/src/styles.css` con `@source`; revisar clases completas representativas y exclusiones. El modo standalone no admite dependencias npm ni plugins de terceros: si un proyecto los necesita, debe abrir un cambio de alcance y evaluar el modo npm.

Con configuración aislada, el comando comprobado es `python manage.py tailwind --settings=core.test_settings build` (settings antes de build). Cambiar valores existentes de [tokens.css](../web/static/css/tokens.css) no exige build; nuevas clases/fuentes sí. Ver [personalización](PERSONALIZACION_VISUAL.md).

No hace falta recompilar por añadir Markdown.

## Evidencia según el cambio

| Cambio                    | Comprobación pertinente                                                           |
| ------------------------- | --------------------------------------------------------------------------------- |
| Regla de negocio          | Entradas válidas/inválidas y límites con datos ficticios                          |
| Permisos                  | Acceso permitido/denegado directo a URL; anónimo, roles y superusuario según spec |
| Escrituras relacionadas   | Integridad, duplicados y fallos parciales/concurrencia cuando corresponda         |
| Interacción de formulario | Navegador, errores, teclado, móvil, estado al volver                              |
| PDF o exportación futura  | Contenido, privacidad y documento corto/extenso si aplica                         |
| Solo documentación        | Enlaces, rutas, fases, requisitos, ausencia de código modificado                  |

En cada resultado distinguir ejecutado, inspeccionado estáticamente, pendiente o no aplicable.

## Entorno actualizado de esta entrega — 2026-10-02

.venv anterior conservado; usar .venv-actualizada/Scripts/python.exe, Python 3.12.14 y lock de 005. Instalación con --require-hashes (52 paquetes), pip check y suite aislada comprobados. No copiar entornos entre máquinas ni importar settings normal para probar. [Procedimiento de instalación/lock/preflight/restauración y opcionales](DEPENDENCIAS.md). La guía no autoriza ejecutar migraciones sobre esta base existente.

## Entorno vigente de esta copia — 007, 2026-10-06

El propietario confirmó **.venv**; la ruta histórica .venv-actualizada corresponde a la base anterior. .venv/Scripts/python.exe funciona con Python 3.12.14 disponible en runtime local de Codex; reconstruido en la misma ruta porque el intérprete copiado faltaba, conservando paquetes y pyvenv.cfg original en .recovery-007. Al cambiar equipo/runtime, recrear con Python propio e instalar el lock con hashes.

Suite vigente: `python manage.py test UsuarioApp homeApp PlanesApp --settings=core.test_settings`, 117 métodos OK. Lock de 54 paquetes coincide con instalación; check/esquema/pip/build OK. [Guía de desarrollo/Google](PLANESAPP_DESARROLLO.md) y [validación 007](../specs/007-planes-app/validation.md). No se importó settings normal ni se aplicaron migraciones a DB existente.


## CuidadosApp 009

Entorno .venv confirmado; no dependencias nuevas. Suite actual: `.venv/Scripts/python.exe manage.py test UsuarioApp homeApp PlanesApp CuidadosApp --settings=core.test_settings`. Check/makemigrations --check/Tailwind también con core.test_settings. 158 tests OK y 89 HTML; [validación](../specs/009-cuidados-cuidadores/validation.md), [guía de uso y migraciones pendientes](CUIDADOSAPP_DESARROLLO.md). Ensayo SQLite efímero de catálogo/reversión y carrera sobre último cupo no equivale a aplicar esquema en DB existente ni a comprobar backend productivo. Preview/helper descartables retirados.


## Aplicación móvil — actualización 2026-10-19

010 en macOS usa .venv-mobile (Python3.12, requirements.txt existente), .venv-edge independiente y Flutter3.47.7 temporal en /tmp/vigia-flutter-sdk. Ejecutar manage.py test UsuarioApp homeApp PlanesApp CuidadosApp --settings=core.test_settings. Demo SQLite explícita separada. Ver [guía](MOVIL_DESARROLLO.md).
