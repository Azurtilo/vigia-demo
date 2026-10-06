# Plan — 005 / Dependencias

Fecha: 2026-10-02. Plan posterior a [spec](spec.md), implementación autorizada por instrucción posterior del propietario y P-005-01 confirmada expresamente. Mantener axes/preventconcurrentlogins comentados y desactivados según nueva instrucción explícita. Resultados en [validation.md](validation.md).

## Base inspeccionada

main / 6bc1bd4, fuente de evidencia en [auditoría](../../docs/VALIDACION_PREPRODUCCION.md). 47 pins actuales instalados en venv aislado Python 3.12.14, pip check sin conflictos, 57 pruebas y 60 plantillas correctas. `.venv` normal roto. No lock con hashes; herramientas/transitivas/opcionales mezcladas en requirements.txt. Django 5.1.2 fuera de soporte; allauth 0.62.1, Pillow 11.3.0 y scripts CDN requieren revisión/actualización. Aislamiento limpio evita el conflicto global cffi/cryptography registrado en entregas anteriores.

## Versiones y pasos técnicos propuestos

1. Reconfirmar avisos/versiones al implementar, conservar estado local y recuperar solo fuentes necesarias, excluyendo secretos/DB/media. Fijar Python 3.12 mantenido como entorno verificado; no cambiar Python del sistema.
2. Resolver P-005-01 con sus efectos concretos antes de cambiar allauth. Revisar notas incompatibles entre 0.62.1 y 65.19.7, y Django 5.1 → 5.2. Ensayos deberán incluir correos con mayúsculas, direcciones que colisionan al normalizar, principales múltiples y autenticadores existentes; el plan no borra/normaliza datos por iniciativa propia.
3. Preparar entradas directas documentadas (`requirements.in`, propuesta nueva), conservando paquetes opcionales actualmente declarados y su inactividad. Separar lógicamente grupos de uso en entradas/documentación; no retirar capabilities de D-008. Generar requirements.txt como lock íntegro con hashes desde resolver aislado, sin freeze global. Si el compilador de lock añade herramientas, registrarlas separadas del entorno de aplicación.
4. Candidatas base: Django 5.2.17, allauth 65.19.7, crispy-forms 2.7, environ 0.14.0, Pillow 12.3.0, requests 2.34.2, urllib3 2.8.0, Jinja2 3.1.6, sqlparse 0.6.0; restantes según inventario. La resolución preliminar **solo de los 47 paquetes actuales actualizados** pasó con pip --dry-run; no es validación de ejecución. Mantener tailwind/django-tailwind/crispy-tailwind actuales al ser compatibles en esa resolución.
5. Añadir bcrypt compatible (candidata 5.0.0) para el hasher ya configurado; probar BCryptSHA256 con Unicode/contraseña larga, verificación y actualización a Argon2. Evaluar extra oficial `django-allauth[mfa]`: qrcode<9 y fido2<3 figuran en metadatos nuevos. Declarar únicamente el conjunto necesario y resuelto; si se instala extra, mantener tipos actuales TOTP/recovery explícitamente y no habilitar WebAuthn/passkeys. Auditar todas las transitivas nuevas antes de cerrar el lock; resolverlas no basta.
6. Instalar el conjunto propuesto en nuevo entorno local aislado y adaptar configuración/API/templates/pruebas en cambios pequeños. allauth reemplaza ajustes antiguos de login/signup; expresar la equivalencia del contrato actual (username/email, registro público cerrado y correo opcional según flujo existente), sin activar verificación obligatoria ni cambiar campos por comodidad. Revisar la detección de IP de nuevas versiones: no confiar en headers de cliente; documentar proxies por entorno sin inventar un hosting.
7. Mantener APIs Django para hash/CSRF/sesiones y política 004. Revisar el subprocess MFA existente: no retirarlo hasta demostrar que el nuevo allauth no contamina modelos de socialaccount desactivado y que login+TOTP y cascada pasan juntos. No añadir socialaccount para esconder ese efecto lateral.
8. Scripts: versiones consultadas Alpine 3.17.4, DOMPurify 3.4.16 y ECharts 6.1.0. Preferir las URLs exactas actuales de CDN con SRI calculado sobre los bytes completos y crossorigin=anonymous, documentando fuente/hash. Comprobar respuesta e integridad en navegador; si CDN no publica artefacto verificable compatible, usar archivo local con origen/hash/licencia. No eliminar capacidades de modal/Alpine por ausencia de usos observados ni imponer CSP nueva en esta spec.
9. Repetir validación del conjunto instalado, integración y navegador. Actualizar documentación/estado y auditoría de dependencias; no cerrar AUD-004/005 ni aceptación del propietario por tests verdes.

## Archivos e integración por requisito

| RF | Archivos existentes / propuestos | Motivo y verificación |
|---|---|---|
| 01/05 | requirements.txt; propuesta requirements.in y docs/DEPENDENCIAS.md | Pins/lock/hashes, clasificación y procedimiento; instalación limpia/pip check/OSV |
| 02 | core/common_settings.py, settings.py; UsuarioApp forms/adapters/views/tests; homeApp/tests.py si afectado; templates/account y templates/mfa | Ajustes/API equivalentes solo donde lo requiera upgrade; regresión auth/permisos/MFA y todos los hashers normales |
| 03 | Migraciones distribuidas por allauth; UsuarioApp/tests.py o fichero de pruebas pertinente dentro de la app | Ensayar puente versión antigua/nueva en DB efímera; no editar migraciones de terceros ni crear migraciones propias sin necesidad detectada y explicada |
| 04 | templates/components/Layout/base.html, templates/pages/index.html; static/vendor solo si se justifica | Pin/SRI o recursos locales; menús/dialogs/gráfico/mensajes y fallo de proveedor |
| 06 | tests afectados, docs/VALIDACION_PREPRODUCCION.md, docs/TRAZABILIDAD.md, docs/VERIFICACION.md y docs/ESTADO_PROYECTO.md; validation.md | Resultados vinculados a commit/diff/hash, RF y límites |

No renombrar apps/modelos/rutas/layouts; reutilizar las pruebas y formularios existentes. Cambiar CSS generado solo si un ajuste de templates/classes lo requiere; build standalone con fuentes existentes. Si se agregan clases, usar nombres completos y comprobar @source. No agregar dependencias npm.

## Migraciones y recuperación

La lectura estática del wheel oficial, con hash PyPI verificado, muestra cinco migraciones nuevas (account.0006–0009, mfa.0003); también hay cambios en tres ficheros anteriores que requieren comparación semántica. Esto no significa reaplicar migraciones ya instaladas. Django 5.2 y otras dependencias deben inspeccionarse de igual manera para detectar operaciones adicionales.

Antes de ejecutar las nuevas migraciones en datos sintéticos, fijar expectativas y P-005-01: no resolver colisiones borrando cuentas, emails o factores. Si el ensayo descubre un efecto nuevo/no acordado, detener la parte afectada y actualizar propuesta. Cargar estado/modelos de la versión anterior en un entorno efímero independiente, registrar fixtures sintéticas, luego verificar estado tras upgrade en segundo entorno; no cargar dos versiones de Django/allauth en el mismo proceso.

Rollback: restaurar el conjunto de paquetes/lock/código anterior y, si hubo migraciones de datos, restaurar respaldo coherente de DB/media en el entorno autorizado. `RunPython.noop` de account.0006/0008 impide recuperar los valores originales con simple migrate backwards. No prometer reversibilidad total. No se aplicará ni revertirá nada en la DB actual; la 0002 propia sigue bajo las restricciones de 003.

## Pruebas previstas en la fase documental

La lista siguiente conserva el plan inicial. Los resultados ejecutados posteriormente y sus límites están en [validation.md](validation.md).

- Instalación limpia sin globales, pip check, fuentes/artefactos/hash de lock y consulta de avisos para todos los paquetes instalados, incluidas transitivas/extras nuevas.
- Suite 57 métodos recibida como regresión, más pruebas pertinentes ante cambios concretos: login username/email válido/inválido, cierre público, registro/perfil actuales, límites por actor/destinatario, POST/CSRF, reset sin correo, sesiones y MFA con factores preservados. No sustituir casos por checks de framework vacíos.
- Hashers normales con datos ficticios, contraseña inválida/Unicode/larga y login con hash heredado sintético; MD5 solo para suite rápida. Mantener registros/evidencia sin valores de contraseña/hash/token.
- Migración sobre base vacía y con emails/autenticadores sintéticos equivalentes a la versión antigua; normalización, selección de principal, colisiones y constraints; ensayo/recuperación sin datos reales.
- `python manage.py check --settings=core.test_settings`; `makemigrations --check --dry-run` y `test UsuarioApp homeApp` con ese settings. Deploy check con valores normales reproducidos, no .env.
- `python manage.py tailwind --settings=core.test_settings build` cuando cambien fuentes. Compilación de templates y verificación de que no se pierde clase propia.
- Navegador móvil/escritorio y ambos modos: menús/dialog/foco/notificaciones, login/perfil/MFA/formulario administrativo y gráfico. Verificar SRI y degradación de CDN; no introducir nuevas credenciales por herramienta cuando su política requiere intervención del usuario. Registrar cualquier parte manual pendiente.

## Límites y documentos

### Ajustes técnicos realmente ejecutados

52 paquetes fijados con hashes, incluyendo extra MFA oficial y pip 26.2.1. Compilador independiente pip-tools 7.6.1: 7.5.3 no funciona con pip moderno. Normalización y recuperación autorizadas y probadas entre entornos antiguos/nuevos; preflight persistente de solo lectura en `UsuarioApp/management/commands/verificar_actualizacion_allauth.py` para detectar colisiones antes del paso afectado (RF-005-03). No endpoint ni migración propia nuevo.

MFA_FORMS apunta a rutas actuales; ACCOUNT_LOGIN_METHODS/SIGNUP_FIELDS expresan el contrato anterior. MFA_ALLOW_UNVERIFIED_EMAIL=True conserva activación sin verificación de 0.62.1, con registro público cerrado; tipos TOTP/recuperación explícitos. Se retiró el subprocess del test MFA tras comprobar login+TOTP y cascada en la misma suite; socialaccount sigue desactivado. Migraciones y pruebas de compatibilidad en tests_dependencias.py; fixes funcionales AUD-004/005 corresponden a 006, aprobada aparte posteriormente.

AUD-004/005 no pertenecen a esta spec y fueron corregidos posteriormente por 006 con autorización propia. No se considera lista para todos los proyectos/hostings por validar SQLite. Documentar revisión manual mensual de avisos, trimestral de mantenimiento y antes de cada nueva copia; parches compatibles prioritarios, actualización de serie antes de EOL con esta misma secuencia SDD. Sin scheduler ni cambios a otros repositorios.

Actualizar índice, estado/proyecto, decisiones y trazabilidad al documentar; comandos/resultados por RF en validation.md al implementar. Propuesta técnica puede ajustarse por metadatos/release notes nuevos, con motivos y autorización vigente; no marcarla aprobada ni alterar RF para legitimar un fallo.
