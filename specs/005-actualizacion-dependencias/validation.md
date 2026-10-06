# Validación — 005 / Actualización de dependencias

Fecha: 2026-10-02. Implementación autorizada y ejecutada; P-005-01 confirmada. Detalle de esta fase debajo. Se conserva la validación documental inicial como antecedente, no como descripción del código actual.

## Antecedente DOCUMENTAR

La [auditoría independiente](../../docs/VALIDACION_PREPRODUCCION.md) revisa la versión vigente main/6bc1bd4. Ejecutó instalación aislada de los 47 pins actuales, 57 pruebas correctas, check/esquema/build/60 plantillas y diagnóstico sintético; encontró bloqueadores. Ninguno de estos resultados valida todavía las versiones futuras de 005.

Para planificar se consultaron PyPI/npm/OSV, se resolvieron 47 candidatas con pip --dry-run sin instalarlas y se leyó el wheel oficial de allauth con hash verificado. Se identificaron cinco migraciones nuevas y efectos de datos con reversión noop. P-005-01 permanece pendiente; no se aplicaron esas migraciones.

Spec creada antes de plan y tasks, seis RF y siete tareas de implementación pendientes. No se modificaron código, pruebas versionadas, requisitos instalables, migraciones propias, CSS de producto ni skill del usuario. El estado de conservación/enlaces del cierre queda en [evidencia global](../../docs/evidencia/auditoria-20261002/cierre.json).

Pruebas del conjunto nuevo, nuevos hashers/transitivas, migraciones de upgrade, navegador con scripts nuevos y reauditoría de esa implementación: **no ejecutadas**. Aceptación funcional y autorización posterior: pendientes. No hay despliegue/commit/push ni intervención sobre datos reales.

## Implementación posterior autorizada — resultados actuales

Git main/6bc1bd4 con cambios sin commit; inicialmente los documentos de auditoría y skill del propietario estaban modificados/sin seguimiento y se conservaron. Recuperación acotada de 204 archivos en .recovery-005, sin .env/DB/media. Python 3.12.14, .venv-actualizada, aislamiento completo sin paquetes globales; .venv anterior intacto. Exclusivamente core.test_settings, SQLite ficticio/memoria, correo/caché locales y archivos temporales.

| RF | Ejecución / resultado | Evidencia |
|---|---|---|
| 01 | 49 entradas revisadas, 52 paquetes instalados con hashes; Django 5.2.17 LTS, allauth 65.19.7, Pillow 12.3.0; 47 paquetes originales conservados | requirements.in/requirements.txt; [instalación oficial](../../docs/evidencia/actualizacion-20261002/instalacion-final.json), pip check sin conflictos |
| 02 | Login usuario/email, signup cerrado, MFA TOTP/recovery, sesiones, correo y jerarquía 004 preservados; cinco hashers normales con bcrypt/Unicode/longitud y actualización Argon2 | tests_dependencias.py, regresión tests.py: login/recovery/password/reset/MFA/sesiones; 76 métodos en conjunto con 006 |
| 03 | Cinco migraciones nuevas inspeccionadas y ejecutadas en fixtures; tres previas con cambios de sintaxis/imports equivalentes, no se reaplican sobre historial existente | [diff](../../docs/evidencia/actualizacion-20261002/migraciones-previas-diff.txt), [upgrade](../../docs/evidencia/actualizacion-20261002/migracion-normal.json), [colisión](../../docs/evidencia/actualizacion-20261002/migracion-colision.json), [restauración](../../docs/evidencia/actualizacion-20261002/restauracion-normal.json) y tests de constraints/códigos heredados/preflight |
| 04 | Alpine 3.17.4, DOMPurify 3.4.16, ECharts 6.1.0, URLs exactas/SRI SHA-384/crossorigin | [bytes/hashes](../../docs/evidencia/actualizacion-20261002/frontend.json), navegador gráfico/menús/modo; [CDN bloqueado](../../docs/evidencia/actualizacion-20261002/inicio-sin-cdn.png) |
| 05 | Lock íntegro incluyendo instalador; pip-tools independiente; nueva guía/manual periódico, opcionales intactos/comentados | [DEPENDENCIAS.md](../../docs/DEPENDENCIAS.md), audit del conjunto real, normal settings idéntico a snapshot |
| 06 | Suite, checks, esquema, templates, build, navegador y documentos con evidencia | [tests](../../docs/evidencia/actualizacion-20261002/tests.txt), [verificación](../../docs/evidencia/actualizacion-20261002/verificacion.json), [build](../../docs/evidencia/actualizacion-20261002/build.json), cierre/manifiesto |

Comandos efectivos: .venv-actualizada/Scripts/python.exe -m pip install --require-hashes -r requirements.txt; pip check; manage.py check, makemigrations --check --dry-run y test UsuarioApp homeApp, siempre --settings=core.test_settings. **76 métodos correctos**, cero fallidos/omitidos; 57 recibidos, seis nuevos de dependencias y trece de integridad 006. Matrices/subtests no inflan ese conteo.

Compilación de **61 HTML** de templates/theme, sin errores. Tailwind standalone 4.3.0 compiló copias aisladas de fuentes, CSS 13.829 bytes idéntico al entregado (SHA-256 d0bcaf37bfd2867e3cb1685bca05cdccd6fb35d1ae12e1eda1d58b380f25347a). Deploy check reproduce defaults normales con host/clave ficticios, sin importar settings.py: conserva **security.W005/W021** por HSTS subdominios/preload desactivados hasta conocer dominio/hosting. No se silenciaron avisos ni se comprobó TLS/proxy real.

Consulta OSV de **52 distribuciones Python instaladas + tres scripts npm: cero coincidencias devueltas**, con fecha/versiones/resultados en [audit-instaladas-final.json](../../docs/evidencia/actualizacion-20261002/audit-instaladas-final.json). No garantiza ausencia de vulnerabilidades futuras ni certifica toda la aplicación. Todos los 52 artefactos del reporte final provienen de files.pythonhosted.org, instalados verificando hashes.

## Adaptaciones y fallos resueltos durante la ejecución

El pip inicial 25.0.1 del nuevo venv devolvió avisos (12 registros brutos con aliases); se fijó/instaló 26.2.1. pip-tools 7.5.3 falló con pip nuevo por stdlib_pkgs retirado; 7.6.1 generó el lock correcto. --allow-unsafe incluye hashes de pip, sin añadir compilador a la aplicación. El primer lock sin esa opción excluía el instalador; instalación final corresponde al lock corregido.

MFA_FORMS y cálculo de TOTP en tests cambiaron de API; los dos errores iniciales se corrigieron conservando escenarios. Se eliminó el subprocess tras comprobar que allauth nuevo importa socialaccount solamente si hay sociallogin real; login+TOTP y cascada pasan en la misma suite. No se activó socialaccount. MFA_ALLOW_UNVERIFIED_EMAIL=True conserva la capacidad anterior con correo opcional; tipos TOTP/recovery explícitos, sin passkeys.

Preflight de solo lectura persistente: verificar_actualizacion_allauth, sin direcciones ni credenciales en salida. Bloquea colisiones y estados MFA desconocidos; no borra/fusiona datos. Una prueba forzando colisión en el executor de SQLite produjo error adicional de limpieza de transacción; se sustituyó por la prueba pertinente de preflight que evita migrar y conserva los datos. La colisión no se solucionó borrando datos reales; la limpieza del registro agregado pertenece únicamente a la fixture del test. Restauración entre entornos antiguos/nuevos comprobada desde snapshot sintético, recuperando mayúsculas/principales y factores. Código de recuperación generado con 0.62.1 permitió login después del upgrade.

## Navegador y límites

Preview local 127.0.0.1:8765 solo con cuentas ficticias/DB en memoria. Inicio/gráfico/modo oscuro y menú de cuenta con SRI, listado/Registro por cargos, ADMIN sin opción ADMIN, MANAGER solo RESTRICTED, root sin cargo sin Registro/acciones, pantalla MFA. Vista móvil solicitada 375×812, sin desbordamiento observado; no nueva certificación de todos los anchos históricos. CSP de preview bloqueó CDN: aviso de gráfico y menú móvil siguen funcionando. Errores CSP fueron intencionales.

Crear/cambiar una nueva credencial por UI requiere intervención del propietario según la política del navegador; se comprobó el guardado completo en servidor y se dejan esos pasos manuales, sin introducir contraseñas nuevas en la herramienta. Aceptación funcional/visual, TLS/proxy, activación de opcionales, cifrado de semillas, auditoría operativa, cache compartida, respaldos reales y concurrencia no se certifican.

Las correcciones funcionales AUD-004/005 son de [006](../006-integridad-registro/validation.md), aprobada aparte. No migraciones propias nuevas, bases reales, .env, media personal, despliegues, commit/push ni cambios a otros proyectos. Evidencia anterior preservada. Conclusión en el alcance corregido: **sin bloqueadores detectados en lo verificado**, con evidencia operativa insuficiente para recomendar producción de un derivado. Siguiente paso: revisión manual y preparación de una copia con su contexto/migración autorizada.

Cierre: [manifiesto](../../docs/evidencia/actualizacion-20261002/cierre.json) con hashes de fuentes y estado Git, comparación contra 204 archivos previos y comprobación de enlaces locales. ZIP de recuperación verificado con rutas únicas/hashes originales. Preview detenido/pestaña cerrada y preparación .work-005 retirada, incluyendo entornos intermedios y bases ficticias; .venv-actualizada y respaldo se conservan.
