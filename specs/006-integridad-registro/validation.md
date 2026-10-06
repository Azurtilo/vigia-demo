# Validación — 006 / Permisos e integridad

Fecha: 2026-10-02. Alcance autorizado después de spec/plan/tasks y confirmación P-006-01. Git main/6bc1bd4 con cambios sin commit. Cambios locales previos conservados; recuperación acotada `.recovery-005/antes-implementacion.zip`, 204 archivos seleccionados, sin secretos/DB/media.

## Ejecución y evidencia

Entorno `.venv-actualizada`, Python 3.12.14, Django 5.2.17, lock de 005. Exclusivamente core.test_settings, SQLite en memoria, correo/caché locales y media ficticia. [76 tests](../../docs/evidencia/actualizacion-20261002/tests.txt): 57 recibidos, seis nuevos de dependencias y trece de integridad, todos correctos. Subtests de matriz no se cuentan como métodos adicionales.

| RF | Implementación / resultado | Evidencia |
|---|---|---|
| 01/02 | cargos_asignables, UserRegistrationMixin, formulario con actor y processor compartido; sin IDs mágicos | Matriz de siete actores/cinco cargos (35 POSTs), ADMIN/manager/root con o sin cargo, código desconocido, ID 1 RESTRICTED válido, opciones HTML, cambio de cargo GET→POST; regresión de anónimo/inactivo y test CSRF específico |
| 03 | atomic User/Profile, éxito tras escritura, compensación de archivo nuevo | Fallo antes y después de Profile.save, fallo decodificación, RuntimeError propagado con rollback; no User/foto nuevos persistidos |
| 04 | preparación de foto previa, transacción, borrado viejo on_commit | Fallo después de guardar, storage que escribe y falla, foto anterior/datos preservados; foto 300×300, cambio sin foto no reprocesa; POST inválido sin perfil no crea fila |
| 04, límite | Limpieza posterior fallida conserva perfil válido y registra error sin nombres/rutas | Test fallo delete tras commit: respuesta de éxito coherente, nueva referencia válida, antigua queda para mantenimiento manual |
| 05 | Regresión 001–005, UI/errores existentes reutilizados | Check/esquema sin cambios, 61 HTML incluyendo theme, build Tailwind idéntico; navegador de Registro/listado/MFA/móvil; detalle compartido en validación 005 |

Comandos: `python manage.py test UsuarioApp homeApp --settings=core.test_settings`, check, makemigrations --check --dry-run. Interprete efectivo `.venv-actualizada/Scripts/python.exe`. Ruff de los tres archivos Python nuevos principales pasó; no se afirma limpieza de todo el repositorio.

[Registro MANAGER](../../docs/evidencia/actualizacion-20261002/registro-manager.png): solo RESTRICTED visible. ADMIN muestra solo MANAGER/RESTRICTED; root sin cargo no tiene Registro. UI móvil a 375 px solicitados, contenido 360 px sin desbordamiento observado. Formulario válido/contraseña nueva probado en servidor; completar alta/cambio de credencial por interfaz queda para el propietario debido a la política de la herramienta de navegador. No se introdujeron nuevas credenciales en navegador.

## Fallos durante el trabajo y límites

Las pruebas antiguas esperaban root sin cargo y exclusión de pk=1; únicamente esas expectativas se sustituyeron por P-006-01, conservando pruebas e IDs históricos. Test de modo visual adapta mocks a la nueva preparación de foto y continúa demostrando ausencia de procesamiento. El fallo MFA inicial pertenecía al cambio de API de 005 y se corrigió allí; no se eliminó ninguna prueba para aprobar la suite.

No existe atomicidad distribuida DB/storage. Compensación/borrado verificados en almacenamiento local; errores de limpieza y caída del proceso requieren mantenimiento/recuperación del producto. No se certifican S3, concurrencia PostgreSQL ni permisos intrínsecos de Django admin: la nueva política se aplica al Registro interno de UsuarioApp. Activar/desactivar/reset conserva íntegramente 004.

AUD-004 y AUD-005 corregidos en los flujos evaluados. Sin nueva app, tabla, migración propia, datos reales, producción, commit/push o aceptación funcional automática. Pendiente revisión manual del propietario y preparación operativa de cada derivado.

Último ensayo de límites: username de 150 caracteres y ruta anterior de 197 frente a max_length=100; rechazo confirmado sin escribir datos ([diagnóstico](../../docs/evidencia/actualizacion-20261002/limite-fotografia.json)). Ruta de nuevas fotos acortada mediante user_id + UUID; el caso válido ahora crea User/Profile/foto 300×300. Referencias de fotos previas se conservan, sin migrarlas. Resultado final: 76 métodos (57 + 6 dependencias + 13 integridad).

Estado final de conservación, fuentes y cierre del entorno ficticio: [manifiesto compartido con 005](../../docs/evidencia/actualizacion-20261002/cierre.json). No se reejecutó trabajo concluido al retomar; se contrastaron archivos, tareas autorizadas y evidencia, se verificó respaldo y se completó el cierre documental.
