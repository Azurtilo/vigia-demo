# Validación — 002 / Renovación visual

Fecha: 2026-10-02. [Spec](spec.md), [plan](plan.md), [tareas](tasks.md). El propietario revisó los documentos y autorizó explícitamente **el alcance completo** después de DOCUMENTAR. Código implementado; regresión correcta; T-002-13 parcial y aceptación estética/funcional pendientes.

## Entorno y conservación

- Copia local sin repositorio Git. Se comprobó el estado antes de editar; los 106 archivos de código/recursos/dependencias del inventario inicial no habían cambiado respecto de DOCUMENTAR. No se sobrescribieron cambios posteriores del propietario detectados.
- Recuperación previa: `.recovery-002/antes-implementacion.zip` (189 archivos seleccionados) y `sha256-antes.txt`. Sin `.env`, bases, media personal ni entorno virtual. La auditoría posterior no encontró archivos inventariados eliminados y comprobó por SHA-256 16 contratos/recursos relevantes preservados.
- Sin cambios en models/views/urls, helper/mixin, common_settings/settings/test_settings, requirements, logo/avatar genérico, AGENTS ni constitución. Forms.py cambia únicamente atributos visuales; el processor expone dos nombres desde la misma evaluación de permisos.
- `.venv/Scripts/python.exe` falla porque apunta a Python 3.12 inexistente. Se utilizó el runtime Python disponible de Codex con versiones exactas de requirements.txt instaladas en `.codex-test-runtime`, aisladas del entorno del propietario. No se actualizó requirements ni se reparó su `.venv`.
- Configuración `core.test_settings`: SQLite en memoria, correo/caché locales, media temporal. El preview `.recovery-002/preview.py` preparó cuentas `demo_*` y correos `@example.test`; localhost 127.0.0.1:8765. Su inicialización aplicó migraciones **solo a SQLite efímero**, sin datos reales. DEBUG y loaders sin caché únicamente dentro de ese proceso. El servidor se detuvo al cerrar; las dependencias de prueba se retiraron al finalizar.
- No se leyó `.env`/db.sqlite3/media personal, no hubo producción, despliegue, commit ni push.

## Comandos y resultados

Los comandos Django se ejecutaron con el Python disponible mediante este wrapper equivalente (el runtime embebido necesita sys.path explícito; PYTHONPATH no bastó):

```powershell
$runtimePython = 'C:/Users/Fernando/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$env:PYTHONUTF8 = '1'
& $runtimePython -c "import sys,runpy; sys.path[:0]=['.codex-test-runtime','.']; runpy.run_path('manage.py',run_name='__main__')" test UsuarioApp homeApp --settings=core.test_settings
```

En un entorno virtual funcional, usar los comandos normales siguientes. La carpeta temporal debe instalarse otra vez para repetir el wrapper; no es una dependencia del producto.

| Comprobación ejecutada | Resultado |
|---|---|
| `python manage.py check --settings=core.test_settings` | Sin problemas (0 silenciados) |
| `python manage.py makemigrations --check --dry-run --settings=core.test_settings` | No changes detected; sin archivos de migración nuevos |
| `python manage.py test UsuarioApp homeApp --settings=core.test_settings` | **27 métodos OK**, última ejecución 1,847 s; SQLite en memoria creada/destruida |
| `python manage.py tailwind --settings=core.test_settings build` | Tailwind standalone **4.3.0**, último build 61 ms; CSS generado actualizado |
| Compilación de las plantillas con `get_template` y core.test_settings | **59 HTML** compiladas sin errores |
| `node --check` sobre los JS propios | Cinco archivos sin errores de sintaxis |
| `node specs/002-renovacion-visual/verificar_js.cjs` | **Cinco comprobaciones OK**, emulación de contratos, sin npm |
| `python specs/002-renovacion-visual/verificar_contraste.py` | **27 pares** medidos y dentro de los mínimos; [JSON](evidencia/contraste.json) |
| `quick_validate.py .codex/skills/frontend-design` | Skill is valid! |
| Auditoría `.recovery-002/auditar.py` | Ningún archivo inventariado eliminado; contratos preservados |
| Revisión `.recovery-002/verificar_documentos.py` | 18 documentos, 127 enlaces locales válidos, nueve RF y estados de las 14 tareas consistentes |

Los mensajes 405 GET y 403 sin CSRF en la suite son rechazos **esperados y afirmados** por los tests. No son fallos de la ejecución. No se usa el número de tests como porcentaje de cobertura.

Incidencias resueltas: pip sin red falló inicialmente; la instalación aislada posterior desde PyPI fue autorizada por revisión automática. Pip avisó del conflicto entre cryptography del runtime y cffi declarado; no se cambió la dependencia del proyecto y el flujo MFA completo pasó. `tailwind build --settings=...` no admite ese orden; la ejecución correcta coloca settings antes de build. Una etiqueta inicial de test dirigida a `UsuarioApp.RenovacionCuentaTests` no importó; se ejecutó correctamente `UsuarioApp.tests.RenovacionCuentaTests`. El punto de recuperación se guardó en `.recovery-002/`, al no poder escribirse la ruta interna inicialmente intentada. No quedó ningún bloqueo de aprobación automática.

## Pruebas del servidor y permisos

Se conservan los 15 métodos de CalidadBase, adaptando la expectativa literal del título del gráfico sin quitar la comprobación de demostración. Se añaden 12 métodos:

| Clase / métodos añadidos | Evidencia |
|---|---|
| `RenovacionUsuariosTests` (7) | Matriz por URL y controles, acciones POST/CSRF, protección de propia cuenta/superusuario, filtros y paginación, imagen válida/inválida, pantallas de cuenta sin perfil/cargo y HTML seguro |
| `RenovacionCuentaTests` (3) | Login mantiene next; logout GET no cierra y POST sí; reset envía correo en memoria y cambio de contraseña rechaza entradas inválidas; flujo TOTP completo |
| `RegresionInicioTests` (2 añadidos) | Últimos cinco accesos activos, actividad aproximada y cuentas sin perfil; seis errores renderizan para anónimo y cuenta sin perfil |

Matriz: anónimo, ADMIN, MANAGER, RESTRICTED, sin perfil, sin cargo, staff sin cargo, inactivo y superusuario activo/inactivo. El superusuario sin perfil conserva gestión. Los permisos del servidor se mantienen; botones y registro consultan el mismo helper. Se comprueban altas internas válidas/errores y registro público cerrado en la suite conservada. Las acciones de activación/desactivación rechazan GET y POST sin CSRF.

El test MFA usa autenticadores y códigos sintéticos reales del entorno aislado: activación TOTP, rechazo de código inválido, generación/descarga/regeneración de recuperación, segundo factor inválido/válido y desactivación. No sustituye esa lógica con mocks ni registra secretos en capturas.

Los contratos JS comprueban: gráfico sin animación en preferencia reducida y cambio de preferencia; resize/retorno desde caché; falta de CDN o contenedor; cierre inmediato/foco/scroll en modo reducido; mensajes seguros como texto, errores persistentes y temporizador de éxito. Estas pruebas **no emulan un navegador completo** ni acreditan su preferencia real.

## Revisión de navegador ejecutada

Navegador integrado, usuarios sintéticos y almacenamiento efímero. Interacciones efectivamente comprobadas:

- Login y logout; registro público cerrado; recuperación enviada a backend en memoria y página de confirmación. Acceso final repetido con las plantillas actualizadas. Contraseña y MFA índice revisados; MFA completo verificado en servidor.
- Inicio: actividad real del entorno de prueba separada del gráfico de ejemplo, canvas visible/redimensionado en los cinco anchos. Tabla con scroll local anunciado en móvil.
- Listado: búsqueda `demo_`, paso a página 2 conservando search, activos/inactivos; desactivar cuenta sintética con confirmación y volver a activarla. Abrir/cancelar/Escape no envían acción; foco vuelve al disparador.
- Menú móvil: foco inicial, Tab del último botón al primer control, Escape, fondo inerte, scroll bloqueado/liberado. Al pasar de móvil a 1024 px se cierra y el foco pasa a navegación visible.
- Cuenta desplegable: estado expandido real, Tab a Editar perfil, Escape y foco de retorno.
- Registro con contraseña débil: errores del servidor visibles. Perfil: guardado de nombre sintético, notificación de éxito, selección del avatar genérico, nombre de archivo anunciado y guardado; imagen cargada (300 px) desde media temporal.
- Paletas petróleo/ciruela/cobre editando **solo tokens.css**, sin build adicional. Colores calculados y selección comprobados; capturas de listado ciruela y gráfico cobre. Marca final restituida a petróleo.
- Consultas de consola de las páginas revisadas sin errores/advertencias de la interfaz. No se afirma disponibilidad futura de los CDN existentes.

Se detectaron recursos anteriores en caché y plantillas cacheadas durante cambios en el preview. Se versionaron los recursos propios con `?v=002`; el proceso efímero se reinició con loaders sin caché. Una pestaña dejó de sincronizar; se continuó en una nueva del mismo navegador y se verificaron login, recuperación, cierre público, Inicio y cuenta/MFA finales. Ninguno de estos cambios modifica la configuración productiva.

### Tamaños

[Medición DOM](evidencia/viewports.json) de Inicio, tomada después de aplicar cada ancho; el listado se revisó a los mismos cinco anchos. No equivale a zoom real.

| Viewport | Ancho de página | Ancho del gráfico | Canvas | Overflow de página |
|---:|---:|---:|---|---|
| 360 | 360 | 326 | Sí | No |
| 390 | 390 | 356 | Sí | No |
| 768 | 753 | 695 | Sí | No |
| 1024 | 1024 | 726 | Sí | No |
| 1440 | 1440 | 1142 | Sí | No |

La diferencia de 15 px en ciertos anchos corresponde al espacio reservado para la barra vertical. Algunas capturas inmediatas al cambiar viewport mostraron un render intermedio; se reemplazaron por capturas estabilizadas antes de usarlas como evidencia. Se retiró el override al cerrar la revisión.

### Contraste y personalización

Medición sRGB según luminancia relativa, incluyendo color-mix de selección/hover. [Script](verificar_contraste.py) y [resultados completos](evidencia/contraste.json). Texto normal objetivo 4,5:1, controles/foco 3:1. Bordes suaves son separaciones decorativas; inputs/botones secundarios usan control-border.

| Paleta | Blanco / marca | Marca / selección | Marca / página | Blanco / hover |
|---|---:|---:|---:|---:|
| Petróleo | 5,47 | 4,83 | 5,00 | 7,33 |
| Ciruela | 6,98 | 6,02 | 6,38 | 9,06 |
| Cobre | 7,31 | 6,33 | 6,68 | 9,38 |

Texto secundario/página: 5,79; límite de control/página: 3,44; estados sobre sus fondos: mínimo 5,98. Estos pares medidos no constituyen una auditoría WCAG completa. La [guía](../../docs/PERSONALIZACION_VISUAL.md) explica cómo cambiar marca, elegir texto de contraste y gestionar build/caché.

### Capturas sintéticas

- [Inicio final](evidencia/inicio-final.png), [login final](evidencia/login-escritorio.png).
- Inicio: [360](evidencia/inicio-360.png), [390](evidencia/inicio-390.png), [768](evidencia/inicio-768.png), [1024](evidencia/inicio-1024.png), [1440](evidencia/inicio-1440.png).
- Menú: [360](evidencia/menu-360.png), [390](evidencia/menu-390.png).
- Personalización: [ciruela](evidencia/usuarios-ciruela-1440.png), [cobre](evidencia/inicio-cobre-1440.png).
- [Registro inválido](evidencia/registro-errores.png), [perfil guardado](evidencia/perfil-guardado.png), [recuperación](evidencia/recuperacion.png), [contraseña](evidencia/cuenta-password.png), [MFA sin activar](evidencia/cuenta-mfa.png).

## Pendientes y siguiente paso

T-002-13 permanece parcial:

1. **Zoom real 200 %**: el navegador ofrecía ajuste de viewport, sin API de zoom. El atajo probado no cambió escala; no se contabiliza como verificación.
2. **Movimiento reducido activado en navegador**: sin capacidad de emular esa preferencia ni control nativo del sistema. CSS inspeccionado y contratos JS sí pasaron; falta repetir menú, diálogo, gráfico y carga con la preferencia real.
3. Revisión visual completa de estados alternativos de cuenta/MFA, las seis páginas de error y mensajes largos; renderizado/validación del servidor están comprobados. No confundir existencia de plantillas con registro de nuevos handlers.
4. Aceptación estética/funcional del propietario. `.venv` sigue roto y su reparación no formó parte de este alcance.

Siguiente paso seguro: completar esos casos de navegador en un entorno de desarrollo con datos ficticios y zoom/preferencia disponibles, luego revisar las capturas con el propietario. No hace falta otra autorización de código para el alcance ya concedido. No ejecutar migraciones sobre la base real ni desplegar como consecuencia de esta validación.
