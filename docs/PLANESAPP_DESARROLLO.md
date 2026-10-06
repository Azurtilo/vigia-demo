# Probar PlanesApp y configurar Google

007 implementada el 2026-10-06. [Resultados y límites](../specs/007-planes-app/validation.md). El entorno de esta copia es **.venv**, no .venv-actualizada. No se aplicaron migraciones a db.sqlite3 ni se leyó .env.

## Entorno y comprobaciones aisladas

Desde la raíz en PowerShell:

```powershell
& .\.venv\Scripts\python.exe manage.py check --settings=core.test_settings
& .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=core.test_settings
& .\.venv\Scripts\python.exe manage.py test UsuarioApp homeApp PlanesApp --settings=core.test_settings
& .\.venv\Scripts\python.exe manage.py tailwind --settings=core.test_settings build
```

Las pruebas usan SQLite en memoria y correo local; no leen settings normal. El intérprete copiado apuntaba a una instalación ausente: se regeneró el entorno en su misma ruta, conservando sus paquetes, con Python 3.12.14 disponible en el runtime local de Codex. El pyvenv.cfg original está en .recovery-007, ignorado por Git. Si cambia ese runtime/equipo, recrear .venv con una instalación propia de Python 3.12 e instalar `requirements.txt` con `--require-hashes`; un venv no es portable.

## Instalar en una base de desarrollo

La implementación no autoriza ejecutar pasos contra una DB existente. Antes de hacerlo: identificar entorno/base, tener respaldo restaurable y autorizar esa operación. El preflight allauth de [DEPENDENCIAS](DEPENDENCIAS.md) sigue vigente para una actualización desde versiones antiguas. Sobre una instalación local nueva deliberadamente elegida, aplicar migraciones con el intérprete de .venv antes de levantar Django.

Se incluyen PlanesApp.0001 (esquema), 0002 (cuatro planes/19 beneficios y cargo Cliente público RESTRICTED) y las migraciones oficiales socialaccount de allauth instalado. Si ya hay un cargo llamado Cliente público con otro código, 0002 se detiene sin modificarlo; resolver esa colisión explícitamente. No copiar una DB ni .env de otro cliente.

El backend normal de correo permanece en consola: el enlace de confirmación aparece en la terminal del servidor local. Abrir el enlace recibido para verificar, o reenviar desde «Correo y verificación». La cuenta puede iniciar sesión sin confirmar; métodos, compra y renovación requieren EmailAddress verificado. Login/MFA de operadores heredados se conservan. Las pruebas automatizadas verifican confirmación válida, inválida, vencida y reenvío mediante locmem.

## Google

Crear un cliente OAuth para aplicación web y configurar la pantalla de consentimiento en el proyecto propio. Registrar exactamente el callback del entorno, por ejemplo `http://127.0.0.1:8000/accounts/google/login/callback/` para desarrollo; esquema, host, puerto y barra final deben coincidir. Consultar [allauth Google](https://docs.allauth.org/en/latest/socialaccount/providers/google.html) y [Google OAuth para aplicaciones web](https://developers.google.com/identity/protocols/oauth2/web-server#creatingcred), consultados el 2026-10-06.

Definir **GOOGLE_CLIENT_ID** y **GOOGLE_CLIENT_SECRET** únicamente en el entorno/configuración privada local. core/settings.py activa el proveedor y sus botones solo cuando ambas existen. Se usa APP por entorno, sin crear otro SocialApp duplicado en admin. No guardar credenciales en código, evidencia o chat. Reiniciar el servidor tras cambiar configuración.

Scopes profile/email, PKCE, acceso online, inicio por POST/CSRF y tokens OAuth sin persistencia. Si Google entrega correo coincidente con otra cuenta local, no se fusiona ni autentica por correo: iniciar sesión en esa cuenta y usar «Cuenta de Google» para conectar explícitamente. El proveedor comprueba la identidad y la verificación del correo; no se confía en un campo del navegador.

La suite usa credenciales ficticias y sustituye únicamente intercambio de token/perfil en los callbacks. Prueba alta, ingreso repetido sin demover cargos, colisión, cancelación y estado inválido. **No se realizó un ingreso Google real**; debe ensayarse con la configuración propia antes de dar por aceptada la integración.

## Recorrido del prototipo

Abrir `/accounts/signup/`, crear cuenta local y confirmar el correo de consola. Entrar a `/planes/mi-suscripcion/`: cuenta nueva RESTRICTED y Vigía Free; no recibe acceso al listado de usuarios. Abrir métodos, agregar tarjeta de ejemplo, elegir plan y revisar el total antes de confirmar. Resultado e historial indican siempre simulación.

| Resultado | Número de prueba |
|---|---|
| Visa aprobada | 4242 4242 4242 4242 |
| Mastercard aprobada | 5555 5555 5555 4444 |
| Rechazo | 4000 0000 0000 0002 |
| Fondos insuficientes | 4000 0000 0000 9995 |

Titular **Ana Demo**, vencimiento **12/30**, CVC **123**. Son números ficticios aceptados por la lista cerrada del simulador; no corresponden a una tarjeta de una persona. No ingresar tarjetas reales. Cualquier otro número se rechaza aunque sea válido por Luhn. Actualizar el vencimiento de ejemplo cuando deje de ser futuro. El almacenamiento conserva marca/últimos cuatro/escenario/fecha/titular, sin número completo ni CVC.

Cambiar plan aplica inmediatamente, cobra el valor completo del destino y reinicia el mes calendario; no prorratea. Free es inmediato sin devolución. Cancelar conserva el período pagado hasta su fin; se puede retirar antes del término con tarjeta vigente. Retirar la última tarjeta pide cancelar en la misma operación. Al vencer sin cancelación, «Simular renovación» inicia un mes desde ese momento, sin cobrar períodos atrasados. No hay tareas programadas ni cargos automáticos.

## Reversión y revisión manual

El ensayo de migraciones se ejecutó solo en SQLite en memoria. Revertir 0002 es no-op: conserva catálogo y cargo; revertir 0001 elimina las tablas e historial propios, pero conserva el cargo en UsuarioApp. Desinstalar socialaccount puede eliminar conexiones y afectar cuentas sin contraseña local; recuperar respaldo/código/lock compatibles, no borrar cuentas como compensación.

Pendientes de entorno/aceptación: migración local elegida y autorizada, OAuth real, zoom 200% y preferencia de movimiento reducido en navegador, lectura asistida y revisión del propietario. No se acredita concurrencia en otro motor de datos ni preparación para producción. Las capturas y resultados usan únicamente datos ficticios.
