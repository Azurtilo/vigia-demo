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

Con configuración aislada, el comando comprobado es `python manage.py tailwind --settings=core.test_settings build` (settings antes de build). Cambiar valores existentes de [tokens.css](../static/css/tokens.css) no exige build; nuevas clases/fuentes sí. Ver [personalización](PERSONALIZACION_VISUAL.md).

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
