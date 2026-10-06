# Validación — 004 / UsuarioApp

Fecha: 2026-10-02. Implementación del alcance completo autorizada por instrucción posterior explícita y ejecutada. [Spec](spec.md), [plan](plan.md), [tareas](tasks.md).
Estado: servidor/regresión verificados; navegador parcial y aceptación funcional pendientes. Sin datos reales, despliegue, commit/push o migraciones sobre bases existentes.

## Alcance realmente implementado

- Nuevo permissions.py y AccountManagementMixin: cargo requerido incluso al root, política por destinatario compartida con las filas. ADMIN sobre MANAGER/RESTRICTED; MANAGER solo RESTRICTED para activar/desactivar; solo ADMIN restablece. Destinatarios propios/ADMIN/root/sin cargo inválidos protegidos.
- Administrativo: SetPasswordForm ampliado con reconfirmación del operador, campos obligatorios/autocomplete y strip=False para conservar contraseñas con espacios. Nueva URL/pantalla privada, GET sin escrituras, POST con CSRF/validadores, hash y update_fields=password. Nunca correo/token; no cambio de estado/MFA/cargo/preferencia/fotos.
- Activación/desactivación: POST, 403 por política, 404 de destinatario inexistente para actor autorizado, 405 por GET autorizado, is_active como único atributo guardado e idempotencia.
- Escrituras transaccionales; mensajes de éxito después de salir de la transacción. Fallos previstos IntegrityError/OperationalError usan contexto en 500.html y retorno al listado, sin éxito aparente. No catch general. never_cache y sensitive_post_parameters/sensitive_variables protegen formulario/informes de error.
- Reutiliza layouts/listado/crispy/tokens de 002/003. Sin modelos/migraciones/dependencias de producto nuevos ni cambios de registro/helper global/configuración normal.

## Entorno y conservación

Git main / HEAD 8f9adda. Al iniciar implementación ya había cambios documentales de 004 (ocho archivos y carpeta nueva), conservados; código inicial limpio. Snapshot `.recovery-004/antes-implementacion.zip`: 123 archivos seleccionados y SHA-256, sin .env/bases/media personal. Antes de actualizar documentación, auditoría detectó únicamente seis archivos existentes de código/HTML modificados: UsuarioApp forms/tests/urls/views, listado y 500.html; nuevos permissions.py/restablecer_password.html fuera del snapshot. CSS generado idéntico después del build.

Contratos protegidos idénticos por SHA-256: AGENTS/constitución, requirements, settings/common/test, mixin y rutas raíz, modelos/adapter, home vistas/middleware, tokens e interfaz.js. La auditoría se conserva en .recovery-004/auditoria.json.

.venv/Scripts/python.exe --version falla por Python312 inexistente; no reparado. Runtime Python de Codex con requirements exacto en .codex-test-runtime temporal. Primera descarga bloqueada por WinError10013; revisión automática permitió instalar. pip advirtió incompatibilidad entre cffi declarado 1.17.1 y cryptography global 50.0.1; no se actualizó ninguno ni requirements. El sandbox no podía leer paquetes recién instalados; la verificación aislada se ejecutó con escalación revisada, siempre core.test_settings, SQLite en memoria, correo/caché/media temporales. Ninguna aprobación automática rechazó el trabajo.

Helpers de recuperación de 002/003 mencionados en documentos no estaban presentes al iniciar; se crearon helpers propios 004, sin restaurar cambios del propietario. ejecutar.py obliga core.test_settings y coloca settings antes de build como exige Tailwind. No depende del .env/configuración normal.

## Comandos y resultados ejecutados

Comandos equivalentes mediante runtime de Codex + .recovery-004/ejecutar.py (settings aislado impuesto por el helper):

| Comando / comprobación | Resultado real |
|---|---|
| test UsuarioApp homeApp --settings=core.test_settings | **57 métodos OK**, 43 recibidos + 14 nuevos; dos métodos de gestión ajustados por la política aprobada. Última ejecución: 5,050 s |
| check --settings=core.test_settings | Sin problemas, cero silenciados |
| makemigrations --check --dry-run --settings=core.test_settings | No changes detected; ningún archivo nuevo de migración |
| tailwind --settings=core.test_settings build | Tailwind 4.3.0 standalone OK (68 ms), sin npm; CSS generado no cambió |
| Compilación de todas las plantillas con loader de Django | **60 HTML OK**, sin conectar a la DB existente |
| git diff --check | Sin errores de espacios; avisos LF/CRLF por configuración Git existente, no alterada |

[Resumen de salida de servidor](evidencia/pruebas-servidor.txt). Salidas completas sintéticas conservadas en .recovery-004; no afirmar cobertura porcentual ni aceptación del propietario.

Casos comprobados por servidor: matriz 11 actores × 8 destinatarios (incluida cuenta propia) × tres acciones, con HTML/URL/GET/POST; perfiles/cargos desconocidos/staff/root e inactivos, CSRF válido/ausente, 404, manipulación, cambios entre GET/POST; backend de correo que lanza si envía; contraseñas débiles/incorrectas/omitidas/no coincidentes, espacios del operador, secreto no repoblado/no-cache; conservación de atributos/email/MFA/preferencia/foto/estado inactivo; dos sesiones de destinatario invalidadas y operador conservado, login nuevo; reenvío de estado y rollback tras escritura real seguida de error. GET/listado/cancelación no restablecen contraseñas.

## Fallos detectados y resueltos

1. Primera suite nueva de 56 métodos: 55 OK y error en cascada de modo visual (`no such table: allauth_socialaccount`). Causa inspeccionada: allauth 0.62.1 importa/registra SocialLogin al reanudar MFA aunque socialaccount no esté instalado, antes de aquella cascada. El nuevo caso MFA se ejecuta en subprocess con la misma configuración/base efímera; prueba la activación, restablecimiento, login nuevo y desafío TOTP completos, sin contaminar el registro de modelos de la suite. No se activó socialaccount ni cambiaron dependencias/configuración/negocio. La suite completa pasó tras aislarlo.
2. Primer build con helper añadió settings después de build y fue rechazado por argparse. Helper corregido para colocarlo antes del subcomando; build siguiente OK.
3. Inspección de SetPasswordForm 5.1.2: valida obligatoriedad en clean, pero los campos base son required=False. Formulario ampliado marca ambos required=True para etiquetas/HTML coherentes; tests de campos omitidos añadidos. Reconfirmación usa strip=False para no recortar una contraseña válida; regresión correspondiente pasa.

## Navegador ejecutado — T-004-07 parcial

Preview único 127.0.0.1:8765, SQLite en memoria y usuarios ficticios, iniciado Hidden. Todas las rutas especiales __preview__ existen solo en el helper de demostración; no se añadieron endpoints de producto. Reinicio aislado tras cambio de formulario invalidó las cookies del preview como era esperable; se generó nueva sesión ficticia.

- Listado y formulario en claro/oscuro, anchos 360/390/768/1024/1440: cero desbordamiento horizontal en 20 observaciones. Campos/errores/acciones legibles; nombres extensos y protección de ADMIN/root/cuenta propia. [Datos de observación](evidencia/navegador.json).
- MANAGER sin enlaces de restablecimiento ni gestión de ADMIN/MANAGER/root; desactiva RESTRICTED con confirmación y lo reactiva desde Inactivos. Superusuario sin cargo: cero controles de gestionar/restablecer. [Matriz observada](evidencia/listado-manager.json).
- Teclado Tab entre campos y foco visible de 2 px; Cancelar devuelve al listado; clic de envío vacío enfoca primer campo y bloquea navegación/escritura mediante required. Formulario y cancelación también con CSP script-src 'none'; [observación sin scripts](evidencia/sin-js.json) y [captura](evidencia/sin-js-390.png).
- Errores reales de formulario vacío producidos por Django Client del preview e inspeccionados visualmente en navegador; no se falsificó HTML. [Errores](evidencia/errores-390.png). Formulario [claro escritorio](evidencia/formulario-light-1440.png) y [oscuro móvil](evidencia/formulario-dark-360.png); otras capturas en evidencia.

**Pendiente manual:** introducir una nueva contraseña y completar el envío válido desde la interfaz. La política de la herramienta de navegador reserva al usuario la entrada, confirmación y envío de nuevas credenciales («have them complete the entry, confirmation, and submission steps themselves»); no se ingresaron nuevas contraseñas mediante esa herramienta ni se pidió usar datos reales. Guardado válido, invalidación de sesiones, ausencia de correo y MFA ya están comprobados en servidor. Este límite no se presenta como falta de autorización de código, ya recibida.

No se afirma zoom/autofill/preferencia reducida completos ni una auditoría de concurrencia en PostgreSQL; SQLite no demuestra bloqueos de fila/cambios simultáneos de cargo. Se conservan los límites visuales históricos de 002/003.

## Cierre y siguiente paso

Siete RF conservados; T-004-01 a 06 completas, T-004-07 parcial y T-004-08 documentación entregada/revisión pendiente. Completar comprobación manual de envío válido con cuenta ficticia en entorno de pruebas y revisión funcional del propietario; no repetir autorización de implementación ni preguntas de permisos resueltas. No aplicación real de 0002 de 003 por esta autorización.

Cierre ejecutado: **13 documentos, 150 enlaces locales sin destinos inexistentes**, siete RF, seis tareas completas y dos con pendientes explícitos; 14 métodos nuevos y 14 contratos protegidos idénticos. [Auditoría documental](evidencia/cierre-documental.json). git diff --check sin errores; solo archivos previstos, documentos, recuperación y evidencia sintética nuevos/modificados. Se preservó el trabajo previo sin stage/reset/commit/push.

Pestaña temporal cerrada y viewport restituido. Preview detenido tras comprobar PID 33396/comando; .codex-test-runtime eliminada después de verificar ruta absoluta exacta dentro del workspace y ausencia de enlace/reparse point. Se conservan snapshot, manifiesto, helpers y evidencia; para repetir pruebas se deben preparar de nuevo las dependencias aisladas. No servidor de pruebas activo ni datos de producción, migraciones reales, despliegue, commit/push o modificaciones a secretos/DB existente.

## Antecedente DOCUMENTAR, conservado como histórico

Antes de la instrucción posterior solo se crearon spec/plan/tasks/validation y documentos de contexto. P-004-01/02 confirmadas por el propietario, 12 documentos/105 enlaces locales válidos, siete RF/ocho tareas pendientes y 211 archivos versionados no Markdown idénticos. No hubo código, tests/build/servidor/migraciones en esa fase. Esas cifras no son evidencia funcional ni describen el estado posterior de implementación registrado arriba.
