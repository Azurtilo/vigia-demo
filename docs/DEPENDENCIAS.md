# Dependencias y mantenimiento de la base

Revisión: 2026-10-02. Verificado en Windows, Python 3.12.14 y Django 5.2.17 LTS. [Validación 005](../specs/005-actualizacion-dependencias/validation.md), [integridad 006](../specs/006-integridad-registro/validation.md).

## Instalación reproducible

`requirements.in` clasifica aplicación, opcionales, construcción/desarrollo y transitivas históricas conservadas. `requirements.txt` fija **52 paquetes**, incluidos bcrypt, las transitivas del extra oficial MFA y pip 26.2.1, con hashes SHA-256. Conserva los 47 paquetes anteriores; 38 cambian de versión. Nueve permanecen en la versión consultada, incluidos django-tailwind 4.5.0, crispy-tailwind 1.0.3 y preventconcurrentlogins 0.8.2. No retirar capacidades de otro proyecto por inferencia.

El entorno normal `.venv` recibido apunta a un Python inexistente y se conservó intacto. Para esta entrega existe `.venv-actualizada`, sin paquetes globales. Usarlo desde PowerShell:

```powershell
& .\.venv-actualizada\Scripts\python.exe -m pip check
& .\.venv-actualizada\Scripts\python.exe manage.py test UsuarioApp homeApp --settings=core.test_settings
```

Para una copia nueva, crear un entorno propio con Python 3.12 mantenido y un nombre libre; no sobrescribir un entorno existente:

```powershell
py -3.12 -m venv .venv-nueva
& .\.venv-nueva\Scripts\python.exe -m pip install --require-hashes -r requirements.txt
```

La instalación de paquetes **no migra la DB**. Un entorno virtual no es portable: recrearlo desde el lock al cambiar equipo/ruta. No usar pip freeze del sistema ni copiar `.env`, DB o media de otros productos. El lock incluye hashes de artefactos publicados; en esta entrega se verificó Windows/Python 3.12, no todas las plataformas posibles.

## Actualizar el lock

Si `requirements.txt` vuelve a mostrar versiones antiguas al ejecutar `pip freeze`, se está exportando el entorno desde el que se ejecuta ese comando. `pip freeze` no actualiza paquetes ni reconstruye este lock con hashes. La fuente de versiones es `requirements.in`; generar el archivo mediante pip-tools como se indica abajo. En VS Code seleccionar `.venv-actualizada/Scripts/python.exe`, o usar explícitamente esa ruta en los comandos; activar otro entorno no instala las versiones nuevas en él.

Cambiar versiones de entradas tras revisar soporte, avisos, notas y compatibilidad. Usar otro entorno para el compilador; no añadir pip-tools a la aplicación:

```powershell
py -3.12 -m venv .venv-lock
& .\.venv-lock\Scripts\python.exe -m pip install pip==26.2.1 pip-tools==7.6.1
& .\.venv-lock\Scripts\python.exe -m piptools compile --generate-hashes --allow-unsafe --strip-extras --output-file=requirements.txt requirements.in
```

`--allow-unsafe` incluye pip con hashes: es una clasificación del compilador para herramientas de instalación, no una afirmación de vulnerabilidad. pip-tools 7.5.3 falla con pip 26.2.1 por una API interna retirada; 7.6.1 fue la combinación que generó este lock. Registrar cambios/transitivas, instalar en otro entorno limpio, ejecutar suite/check/esquema/build y reconsultar avisos de **todo lo instalado**, también el instalador. No actualizar el lock sin verificar luego la instalación.

Revisión manual mensual de avisos y trimestral de versiones/soporte; repetir antes de crear cada producto y ante avisos nuevos. Priorizar parches de seguridad compatibles. Django 5.2 LTS tiene soporte extendido hasta abril de 2028 según [Django](https://www.djangoproject.com/download/). Documentar el siguiente salto antes del fin de soporte. No se creó una automatización.

## Opciones y autenticación

Axes y preventconcurrentlogins **siguen instalados y comentados/desactivados** en common_settings (apps, middleware/backend) y settings (opciones). El propietario confirmó esta preferencia. No basta descomentarlos: cada producto debe decidir reglas, revisar configuración de su versión y probar login, bloqueo/desbloqueo, MFA y sesiones. La conservación de preventconcurrentlogins 0.8.2 no demuestra mantenimiento activo ni compatibilidad de su activación con todos los futuros productos.

Allauth 65.19.7 usa ACCOUNT_LOGIN_METHODS y ACCOUNT_SIGNUP_FIELDS; se conserva login por usuario/email y registro público cerrado. Se actualizaron importaciones de formularios MFA. Tipos explícitos: TOTP y códigos de recuperación; no se activan passkeys, WebAuthn ni socialaccount por instalar extras. MFA_ALLOW_UNVERIFIED_EMAIL=True conserva el comportamiento de 0.62.1 en esta base con correo opcional y registro público cerrado. Cada producto debe decidir verificación de correo; no abrir signup público manteniendo esta elección sin revisar su riesgo.

Argon2 sigue siendo el hasher normal inicial; bcrypt instalado permite verificar BCryptSHA256 heredado. Se probaron los cinco hashers normales, Unicode/contraseña larga e inicio de sesión que actualiza hashes a Argon2. MD5 se limita a test_settings. No importar settings.py ni leer el .env para estas pruebas.

Allauth moderno no confía por defecto en X-Forwarded-For. Cada hosting debe definir explícitamente su proxy de confianza antes de ajustar ALLAUTH_TRUSTED_PROXY_COUNT/HEADER; no copiar cabeceras de cliente. SECURE_PROXY_SSL_HEADER de la configuración normal requiere también un proxy verificado. El deploy check simulado no acredita el proxy/TLS real.

## Antes de migrar una instalación existente

P-005-01 confirmado: correos en minúsculas, elección de principal único, índices/constraints y mfa.0003. Se ensayaron versiones antiguas→nuevas, constraints, MFA/códigos heredados y restauración en SQLite ficticio.

Comando **de solo lectura**, que se ejecuta únicamente en un entorno/base autorizado:

```powershell
python manage.py verificar_actualizacion_allauth
```

Cuenta colisiones de correo normalizado por usuario, correos verificados, User.email y principales múltiples, sin imprimir direcciones. Detiene el preflight si hay colisiones; no borra ni fusiona datos. Los duplicados de User.email requieren decisión del propietario aunque el modelo User no imponga unicidad. El comando no intercepta `migrate`: incorporarlo obligatoriamente al procedimiento de actualización y revisar su código de salida.

Conservar un respaldo coherente de código/lock/DB/media y demostrar su restauración en ensayo. En caso de colisiones, detener la migración y acordar corrección de datos; no seguir tras un error ni borrar usuarios para resolverlo. Las migraciones account.0006/0008 tienen reversión noop: `migrate` hacia atrás no restaura mayúsculas ni principales originales. Recuperar el respaldo coherente, también las versiones anteriores. La prueba de colisión forzada mostró además error de limpieza de transacción del schema editor SQLite; el preflight evita entrar en ese estado y el respaldo sigue siendo necesario.

No se ejecutó este procedimiento sobre la base real ni se autorizó migrarla por esta entrega.

## Scripts del navegador

Alpine 3.17.4, DOMPurify 3.4.16 y ECharts 6.1.0 tienen URLs exactas, SRI SHA-384 y crossorigin=anonymous. [Origen, bytes y hashes](evidencia/actualizacion-20261002/frontend.json). No modificar URL sin recalcular/verificar SRI sobre el archivo completo. Se comprobó carga/gráfico y degradación con CDN bloqueado: navegación disponible y aviso del gráfico. No se añadió Node.js; Tailwind standalone 4.3.0 produjo CSS idéntico.

## Fotografías e integridad

La spec 006 prepara fotos nuevas antes de escribir, usa transacciones para User/Profile y compensa archivos nuevos si falla el flujo. La foto anterior se borra después del commit; guardar otros campos no la reprocesa. Se verificó almacenamiento local aislado, incluso error después de escribir y fallo de limpieza tras commit. Si la limpieza falla, se registra un error sin datos de usuario y se conserva el perfil válido; revisar archivos huérfanos manualmente en un entorno autorizado, sin borrar el avatar compartido. No se certifica una transacción distribuida con S3 ni recuperación automática ante caída del proceso.

La política de cargos nueva corresponde al Registro de UsuarioApp. No redefine permisos intrínsecos del sitio Django admin, ni añade un sistema de auditoría/antiabuso/cifrado MFA. Esas decisiones, hosting, respaldos operativos y aceptación manual siguen perteneciendo a cada producto.

La ruta de fotos nuevas usa users/{user_id}/UUID.ext: evita superar los 100 caracteres del campo con un username válido de 150. No mueve fotografías ni cambia referencias ya guardadas. Diagnóstico y regresión de longitud máxima en validación 006.

## Cambio acotado de esta copia — 007, 2026-10-06

La configuración vigente de este derivado abre registro público y habilita Google/socialaccount con correo optional y gate de operaciones en PlanesApp. Conserva MFA heredado y opcionales comentados. Las descripciones de «registro cerrado/sin socialaccount» anteriores son historia de 005, sustituidas en este producto por 007.

Fuente: django-allauth[mfa,socialaccount]==65.19.7. Se añadieron oauthlib 4.0.0 y PyJWT 2.15.1. HEAD recibido tenía 51 pins sin hashes; lock regenerado con pip-tools 7.6.1/pip 26.2.1 en entorno compilador separado: 54 paquetes con hashes, 51 versiones previas conservadas y pip 26.2.1 ya declarado en requirements.in. .venv instalado coincide exactamente y pip check pasa. No se afirma nueva auditoría OSV de estas adiciones.

Usar **.venv/Scripts/python.exe** en esta copia; se reparó su intérprete ausente sin borrar paquetes. [Guía](PLANESAPP_DESARROLLO.md), [evidencia](../specs/007-planes-app/evidencia/verificacion.json). No migración real ni instalación en producción; configuración Google externa pendiente, sin secretos guardados.
