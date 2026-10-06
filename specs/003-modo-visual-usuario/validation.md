# Validación — 003 / Modo visual por usuario

Fecha: 2026-10-02. Alcance completo autorizado por instrucción posterior del propietario. Código implementado; validación visual parcial y aceptación pendientes. [Spec](spec.md), [plan](plan.md), [tareas](tasks.md).

## Cambios y entorno real

Botón sol/luna en Inicio; POST/CSRF, cuenta activa y propietario de sesión; UserVisualPreference con relación única y restricción light/dark; processor de lectura y HTML inicial; tokens de ambos modos, estados/gráfico y QR. Sin app/dependencias nuevas, cambios de cargos ni procesamiento de fotos. 400/500 presentan rechazo/fallo legible.

Git main con numerosos cambios previos de 002, conservados. Snapshot acotado `.recovery-003/antes-implementacion.zip` con 123 archivos y manifiesto SHA-256 anterior; rutas relativas, sin .env/DB/media personales. Auditoría `.recovery-003/auditar.py`: ninguna eliminación; AGENTS/constitución/requirements, settings normal/aislado, core.mixins/rutas y homeApp vistas/middleware idénticos. Las modificaciones de código observadas pertenecen al mapa de 003, incluidos los dos errores y CSS generado. No stage/commit/push.

`.venv/Scripts/python.exe --version` volvió a fallar: Python312 de su configuración no existe. No se reparó .venv. Se usó el Python del runtime de Codex y requirements.txt exacto en `.codex-test-runtime`; sin modificar el runtime global. Primer pip bloqueado por red del sandbox (WinError 10013), segundo con revisión automática permitió la descarga. Pip emitió aviso por cryptography global y cffi fijado; las pruebas de las dependencias temporales pasaron. No se actualizaron versiones para ocultarlo.

`core.test_settings` no importa settings.py ni .env: SQLite en memoria, media/correo/caché temporales. Generación, aplicación/reversión de 0002 solo ahí. No se abrió la base existente ni se aplicó migración real. Código normal requiere esa tabla antes de poder guardar; acordar entorno/respaldo y autorizar la aplicación por separado. Rollback pierde preferencias y conserva cuentas/perfiles; probado en SQLite descartable.

## Comandos y resultados ejecutados

Los comandos Django se ejecutaron con el Python del runtime y `.recovery-003/ejecutar.py`, que añade la carpeta temporal a sys.path y exige explícitamente `--settings=core.test_settings`. Equivalentes de manage.py:

```powershell
python manage.py makemigrations UsuarioApp --name user_visual_preference --settings=core.test_settings
python manage.py test UsuarioApp homeApp --settings=core.test_settings
python manage.py check --settings=core.test_settings
python manage.py makemigrations --check --dry-run --settings=core.test_settings
python manage.py tailwind --settings=core.test_settings build
```

| Comprobación | Resultado real |
|---|---|
| makemigrations autorizado | 0002, un único CreateModel con FK única/choices/check; ninguna modificación a User/Profile/Position |
| Regresión antes de ampliar tests | 27 métodos anteriores OK |
| Suite final | **43 métodos OK**: 27 anteriores, uno de MFA ampliado, y 16 nuevos; 2,304 s. [Log](evidencia/django-tests.log) |
| check | Sin problemas, cero silenciados |
| makemigrations --check --dry-run | No changes detected |
| tailwind build | Standalone 4.3.0 OK; última compilación después de QR/hover |
| .recovery-003/auditar.py | 123 archivos anteriores, ninguna eliminación, contratos protegidos idénticos; **59 HTML compiladas** |
| node specs/002-renovacion-visual/verificar_js.cjs | **5 contratos JS OK**, incluidos animación reducida, resize/caché, fallback y diálogo. Emulación; no navegador con preferencia reducida real |
| python specs/003-modo-visual-usuario/verificar_contraste.py | **180 pares sRGB correctos** desde tokens reales; petróleo/ciruela/cobre en claro/oscuro. [Mediciones](evidencia/contraste.json) |

Primera suite ampliada: un fallo de fixture por cuenta sin contraseña, allauth redirigía a establecerla; se añadió contraseña sintética al fixture y se preservó el contrato de autenticación. Repetición/final correctas. Respuestas 400/403/405/500 y ProgrammingError sintético del log son escenarios esperados de pruebas, no fallos de la suite.

Contraste: la primera medición encontró hover ciruela oscuro 4,34:1; se corrigió mezcla hacia blanco al 12 % y se repitió la auditoría. QR negro sobre superficie oscura detectado visualmente y corregido con --qr-surface blanco/padding, sin invertir ni regenerar imágenes. No se alteraron RF para legitimar esos defectos.

## Cobertura del servidor por RF

| RF | Evidencia ejecutada |
|---|---|
| RF-003-01 | RegresionInicioTests.test_selector_inicial_y_modo_servidor_en_pantallas_compartidas: formulario, CSRF, botón/nombre/estado y atributo inicial; teclado en navegador |
| RF-003-02 | ModoVisualTests: primer guardado, GET sin filas, logout/login/cliente nuevo, A/B mismo navegador, unicidad/reintento; no crea Profile |
| RF-003-03 | Matriz ADMIN/MANAGER/RESTRICTED/sin cargo/sin perfil/staff/root; inactivos incluido root rechazados usando backend de prueba que permite alcanzarlos; anónimo, GET405, CSRF403/válido, entradas inválidas400, IDs ajenos y next ignorados; constraints/cascada |
| RF-003-04 | HTML servidor, usuarios/correo/contraseña/MFA; seis errores con modo propio; login público y MFA antes de autenticarse claros, después oscuro; gráfico/token en navegador |
| RF-003-05 | 180 contrastes, diez tamaños Inicio (cinco por modo), marcas y QR. Zoom/preferencia reducida/autofill real pendientes |
| RF-003-06 | Fallos OperationalError/IntegrityError no alteran valor ni muestran éxito; ProgrammingError no ocultado. Sin ejecución de scripts: formulario/recarga ambos sentidos |
| RF-003-07 | Suite completa, MFA/TOTP/recuperación, perfiles/fotos/actividad/cargos/filtros recibidos; MigracionModoVisualTests revierte 0002 sin eliminar User/Profile y reaplica tabla vacía; hashes de contratos preservados |

No sumar asociaciones RF como conteo de tests ni afirmar porcentaje de cobertura.

## Navegador y evidencia sintética

Preview normal: `.recovery-002/preview.py`, 127.0.0.1:8765, SQLite en memoria y cuentas demo. IAB: pulsación de luna/sol, Enter/Espacio, Tab/Shift+Tab y foco solid de 3 px; botón 44×44; recarga, logout/login A/B y cuenta sin perfil. Inicio en 360/390/768/1024/1440, claro y oscuro; sin desborde de documento (tabla con scroll propio). Tres marcas en ambos modos; petróleo restituido.

Usuarios, registro, perfil, contraseña y MFA en oscuro; QR sobre blanco, gráfico canvas/leyenda/ejes, resize; consulta de consola sin warnings/errors capturados del preview normal. Es una inspección de estos escenarios, no certificación exhaustiva de todas las pantallas/errores. [Observaciones](evidencia/navegador.json), [Inicio final](evidencia/inicio-final.png), [móvil oscuro](evidencia/inicio-oscuro-360.png), [gráfico](evidencia/grafico-oscuro.png), [QR](evidencia/mfa-qr-oscuro.png).

Preview sin scripts: `.recovery-003/preview_sin_js.py`, 127.0.0.1:8766, base efímera independiente y cuenta demo_sin_js. Cabecera HTTP leída y confirmada: `Content-Security-Policy: script-src 'none'`. Login y selector por formularios nativos; oscuro después de pulsar/recargar, claro después de Enter. Cero canvas del gráfico, coherente con scripts bloqueados. La consola IAB no capturó entradas CSP; la prueba se acredita por cabecera y comportamiento, no por ese log. [Captura](evidencia/sin-javascript-oscuro.png), [resultado](evidencia/sin-javascript.json). No cambió la CSP del producto.

## Pendientes y siguiente paso

- T-003-07 parcial: zoom real 200 %, preferencia reducida activada en navegador, autofill real y revisión visual exhaustiva de estados alternativos de cuenta/MFA/errores/mensajes largos. Las capacidades del IAB usadas ofrecen viewport, sin control expuesto para zoom/preferencia; los contratos emulados no reemplazan esa verificación.
- T-003-08: documentación/entrega preparadas; revisión estética y funcional del propietario pendiente. No se marca aceptación por tests verdes.
- Se conservan pendientes históricos T-002-13. No hubo decisión crítica nueva ni migración de efectos no acordados.
- Completar las verificaciones visuales y revisar esta entrega. Aplicar 0002 sobre la base existente requiere su autorización de entorno/respaldo; no pedir otra vez autorización para implementar el código ya entregado.

Revisión documental ejecutada: `.recovery-003/verificar_documentos.py`, 22 documentos, 175 enlaces locales válidos y cero inexistentes; siete RF conservados, seis tareas completas y dos con pendientes explícitos. No se modificó la skill; su enlace a la guía sigue vigente.

Cierre comprobado: ambos procesos de preview identificados por PID/comando y detenidos; .codex-test-runtime retirada después de verificar su ruta absoluta dentro del workspace. Pestañas temporales cerradas, override de viewport restituido; snapshot/helpers/evidencia conservados. No despliegue, producción ni datos reales.
