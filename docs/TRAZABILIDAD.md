# Trazabilidad de requisitos y pruebas

No hay requisitos de un módulo de negocio todavía. La spec transversal 001-CalidadBase sí tiene implementación y evidencia funcional.

Actualizar al crear una spec y después de verificarla:

## Calidad seguridad base

Spec: [001-calidad-seguridad-base](../specs/001-calidad-seguridad-base/spec.md)

| RF | Tarea | Código o diseño real | Pruebas automatizadas asociadas | Cant. | Otra evidencia | Estado |
|---|---|---|---|---:|---|---|
| RF-001-01 | T-001-01, 02, 05, 09 | `core/common_settings.py`, `settings.py`, `test_settings.py` | `ConfiguracionAisladaTests.test_recursos_de_prueba_estan_aislados`; `test_correo_se_conserva_en_memoria` | 2 | Suite sobre SQLite en memoria y temporales | Verificado |
| RF-001-02 | T-001-03 | Adapter y allauth configurados | Los 3 métodos de `RegistroPublicoTests` | 3 | GET/POST cerrados y cero altas | Verificado |
| RF-001-03 | T-001-04, 06 | Mixin/helper, vistas y processor | Los 4 métodos de `PermisosRegistroInternoTests` | 4 | Matriz GET/POST con roles, estados y superusuario | Verificado |
| RF-001-04 | T-001-05 | Formularios/modelos/vista existentes | Los 4 métodos de `CreacionUsuarioTests` | 4 | Altas válidas y rechazos por datos inválidos | Verificado |
| RF-001-05 | T-001-06, 09 | Processor y `nav.html` | `NavegacionRegistroTests.test_enlace_coincide_con_politica_del_servidor` | 1 | Navegador escritorio/móvil del 2026-09-20 | Verificado |
| RF-001-06 | T-001-07, 08, 11, 12 | `styles.css`, configuración standalone y CSS generado | Ninguna prueba Django específica | 0 | Builds Tailwind 3 (2026-09-20) y Tailwind 4.3.0 (2026-09-22); inspección de fuentes y CSS | Verificado técnicamente |
| RF-001-07 | T-001-01, 08, 09, 10 | Configuración, regresión y docs | Los 2 métodos de `ConfiguracionAisladaTests`; `RegresionInicioTests.test_inicio_conserva_grafico_demostrativo` | 3 | `check`, migraciones, navegador y revisión de diff | Verificado técnicamente |

Durante DOCUMENTAR, rutas y pruebas propuestas deben marcarse «previsto / no ejecutado». Al implementar, registrar rutas reales. Un test de servidor no demuestra por sí mismo la interacción JavaScript ni la legibilidad de un PDF.

## Renovación visual de Base-2 — implementación autorizada

Spec: [002-renovacion-visual](../specs/002-renovacion-visual/spec.md). Diseño: [plan](../specs/002-renovacion-visual/plan.md). Fecha: 2026-10-02. [Evidencia detallada](../specs/002-renovacion-visual/validation.md): 27 métodos Django correctos (15 base, 12 añadidos), cinco contratos JS y comprobación de contrastes. La tabla asocia pruebas sin sumarlas como cobertura.

| RF | Tareas | Código real | Evidencia ejecutada | Estado |
|---|---|---|---|---|
| RF-002-01 | T-002-02, 03, 06, 07, 08, 10, 11, 13 | Layouts, cuenta/MFA, errores, Inicio/listado/perfil | Capturas sintéticas; 59 plantillas compiladas; test_errores_renderizan_para_anonimo_y_cuenta_sin_perfil | Implementado; aceptación visual pendiente |
| RF-002-02 | T-002-02, 04, 05, 07, 09, 10, 11, 12, 13 | tokens.css, @theme inline, CSS/JS/widgets semánticos | Build 4.3.0; tres marcas en navegador; contraste.json | Verificado en los usos medidos |
| RF-002-03 | T-002-03, 04, 13 | nav.html compartido, dialog móvil, interfaz.js | Cinco anchos Inicio/listado; Tab/Escape/foco/cambio a escritorio | Parcial: zoom pendiente |
| RF-002-04 | T-002-05, 06, 07, 08, 09, 12, 13 | Componentes/formularios/confirmaciones | RenovacionUsuariosTests: filtro, imagen, accesos, seguridad HTML; RenovacionCuentaTests (3); navegador perfil/imagen/registro inválido | Regresión OK; revisión visual completa pendiente |
| RF-002-05 | T-002-04, 09, 10, 13 | CSS reducido, interfaz.js y grafico_home.js | verificar_js.cjs: animación reducida/gráfico, cambio de preferencia y cierre inmediato; apertura/cierre en navegador normal | Parcial: preferencia real pendiente |
| RF-002-06 | T-002-03, 04, 05, 06, 07, 08, 09, 10, 11, 13 | Foco, controles/etiquetas, mensajes y responsive | Contrastes 27 pares; teclado y navegación modal en navegador; HTML seguro probado | Parcial: zoom, mensajes largos y revisión visual completa pendientes |
| RF-002-07 | T-002-01, 04, 06, 07, 08, 12, 13 | Helper/mixin preservados; processor y controles compartidos | RenovacionUsuariosTests: matriz, protección propia/superusuario y POST/CSRF; RenovacionCuentaTests: login/logout/reset/TOTP; suite 001 preservada | Verificado en servidor |
| RF-002-08 | T-002-10, 12, 13 | Inicio/gráfico con datos originales y tokens | RegresionInicioTests (3); contratos JS resize/caché/CDN; canvas en cinco anchos | Verificado técnicamente |
| RF-002-09 | T-002-01, 02, 13, 14 | PERSONALIZACION_VISUAL.md y skill local | Recoloración solo tokens; contraste; quick_validate; revisión de enlaces | Documentado; aceptación pendiente |

Resultados detallados de un módulo: `validation.md` en su carpeta. Ver [plantilla](../specs/_templates/validation.md).

## Modo visual por usuario — 003, implementación autorizada

[Spec](../specs/003-modo-visual-usuario/spec.md), [plan](../specs/003-modo-visual-usuario/plan.md), [tareas](../specs/003-modo-visual-usuario/tasks.md), [evidencia ejecutada](../specs/003-modo-visual-usuario/validation.md). Suite total 43 métodos (27 recibidos, uno de MFA ampliado y 16 nuevos). Las asociaciones siguientes no son porcentajes de cobertura.

| RF | Tareas | Código real | Evidencia ejecutada / límite |
|---|---|---|---|
| RF-003-01 | T-003-06, 07 | index.html/form POST/CSRF e iconos | RegresionInicioTests selector; navegador ratón/Enter/Espacio/Tab/foco y cinco anchos por modo |
| RF-003-02 | T-003-02, 03, 04, 07 | UserVisualPreference y processor propio | ModoVisualTests: persistencia A/B/nueva sesión, logout/login, unicidad/reintento, GET sin filas; dos cuentas en navegador |
| RF-003-03 | T-003-02, 03, 07 | Mode choices/check y VisualModeUpdateView | Matriz activa/inactiva/root, propietario, anónimo, 405/403/400, CSRF válido, IDs ajenos/next, constraints/cascada |
| RF-003-04 | T-003-04, 05, 06, 07 | preferencias_visuales, base.html y tokens | Sin perfil/default; páginas/correo/contraseña/MFA, seis errores, login y pre-MFA claros/después oscuro; canvas en navegador |
| RF-003-05 | T-003-05, 06, 07 | Pares de marca/estados y --qr-surface | 180 contrastes, tres marcas en ambos modos, cinco anchos, QR y foco. Parcial: zoom/preferencia reducida/autofill y revisión visual exhaustiva pendientes |
| RF-003-06 | T-003-03, 06, 07 | POST confirmado, 400/500 contextual | Fallos previstos no alteran valor; ProgrammingError no ocultado; formulario y recarga ambos sentidos con CSP sin scripts |
| RF-003-07 | T-003-01, 02, 04, 05, 07, 08 | Base preservada, 0002 y guía | 43 tests/check/migraciones/build, 59 HTML y cinco contratos JS; rollback efímero no borra User/Profile; hashes protegidos. Revisión del propietario pendiente |

Estado: código del alcance completo autorizado e implementado; T-003-07 validación parcial, T-003-08 documentación preparada y revisión del propietario pendiente. No aplicar 0002 a datos reales por esta autorización. Evidencia nueva separada de 002.

## UsuarioApp — 004, implementación autorizada

[Spec](../specs/004-administracion-usuarios/spec.md), [plan](../specs/004-administracion-usuarios/plan.md), [tareas](../specs/004-administracion-usuarios/tasks.md), [validación](../specs/004-administracion-usuarios/validation.md). Propietario revisó documentos/autorizó después el alcance completo. 57 métodos OK (43 recibidos, 14 nuevos; dos métodos de gestión ajustados), sin migraciones nuevas/reales. P-004-01/02 implementadas.

| RF | Tareas | Código real | Evidencia ejecutada / límite |
|---|---|---|---|
| RF-004-01 | T-004-01/04/05/06/07/08 | AdministrativePasswordForm/View, UserPasswordReset y plantilla/listado | AdministracionUsuariosTests.test_restablece_inferiores_sin_email_ni_llamadas_a_correo; matriz GET/POST/HTML; envío válido por UI pendiente manual |
| RF-004-02 | T-004-01/02/03/06/08 | permissions.py y UserDeactivateView | test_matriz_por_destinatario_y_controles_coinciden; estado idempotente; MANAGER desactiva RESTRICTED en navegador |
| RF-004-03 | T-004-01/02/03/06/08 | UserActivateView reutiliza vista de estado y política | Matriz completa/objetivos protegidos; test_estado_idempotente_preserva_otros_atributos; reactivación en navegador |
| RF-004-04 | T-004-01/02/03/05/06/07/08 | AccountManagementMixin/flags por fila, helper global preservado | Matriz, test_anonimo_e_inactivo_no_escriben, test_ids_inexistentes_y_manipulados_no_eluden_autorizacion, test_permisos_actualizados_entre_get_y_post; root requiere cargo |
| RF-004-05 | T-004-01/04/05/06/07/08 | Reconfirmación/validadores/required/strip=False/CSRF/caché y decoradores sensibles | Tests campos invalidos, espacios del operador, csrf/no-store y parametros sensibles; error inesperado no ocultado; foco/required/errores/sin scripts en navegador |
| RF-004-06 | T-004-01/03/04/05/06/08 | update_fields/atomic y hash de sesión existente | Tests dos sesiones inválidas/operador conservado, datos/MFA/preferencia/inactivo, nuevo login+TOTP en subprocess, rollback tras escritura y reenvío |
| RF-004-07 | T-004-01/03/05/06/07/08 | Layouts/tokens/componentes 002/003 y listado existentes | 57 tests de regresión, check/build/esquema, 60 HTML; cinco anchos/ambos modos, teclado y Cancelar. Parcial: envío válido por UI y revisión del propietario |

T-004-01 a 06 completas; T-004-07 parcial y T-004-08 entrega documental/revisión pendiente. Ninguna prueba del ZIP copiada ni porcentaje de cobertura atribuido. MFA aislado por efecto lateral de importación de modelos opcionales allauth 0.62.1; no modifica configuración de producto. Evidencia histórica de 002/003 preservada.

La cantidad cuenta métodos de prueba asociados al RF, no subtests ni aserciones. Un mismo método puede respaldar más de un RF; por eso la suma de esta columna no equivale al total único de la suite ni a un porcentaje de cobertura.

## Auditoría independiente y propuesta 005 — 2026-10-02

La [auditoría global](VALIDACION_PREPRODUCCION.md) relaciona RF/RNF de 001–004 con código/evidencia actual en main/6bc1bd4: 57 tests correctos y hallazgos independientes. No sustituye la aceptación ni cierra tareas visuales históricas. Se conserva su evidencia por spec.

| RF nuevo | Tareas previstas | Diseño / archivos previstos | Estado de evidencia |
|---|---|---|---|
| RF-005-01 | T-005-01/03/06 | requirements.txt, entrada/lock/documentación propuestos | Inventario y resolución preliminar; conjunto nuevo no instalado ni probado |
| RF-005-02 | T-005-02/03/04/06 | Settings/auth/templates/tests afectados, hashers/MFA | Compatibilidad planificada; regresión actual con versiones antiguas |
| RF-005-03 | T-005-02/04/06 | Migraciones terceros/ensayos sintéticos | Wheel leído/hash verificado; P-005-01 pendiente; migraciones nuevas no ejecutadas |
| RF-005-04 | T-005-05/06 | base.html/index.html y scripts exactos/SRI propuestos | Avisos/versiones inventariados; UI con scripts nuevos no probada |
| RF-005-05 | T-005-01/03/07 | Entradas/lock y docs/DEPENDENCIAS.md propuestos | Instalación antigua limpia OK; flujo de lock/mantenimiento nuevo pendiente |
| RF-005-06 | T-005-01/04/05/06/07 | Regresión y docs de validación/estado | Siete tareas pendientes; no implementación autorizada aún |

## Ejecución posterior de 005/006 — 2026-10-02

| RF | Código / tareas | Evidencia actual |
|---|---|---|
| RF-005-01/05 | requirements.in/lock, T00501/03/07 y guía DEPENDENCIAS | 52 artefactos instalados con hashes en venv limpio, pip check/OSV (55 consultas Python+JS sin coincidencias), opcionales desactivados |
| RF-005-02 | common_settings y tests_dependencias/tests, T00504/06 | Username/email, signup cerrado, recuperación/MFA/sesiones/permisos, cinco hashers/upgrade Argon2 y códigos MFA heredados |
| RF-005-03 | comando verificar_actualizacion_allauth y MigracionesAllauthTests, T00502/04 | Colisiones/tipos desconocidos bloqueados sin escritura, normalización/principal/constraints, puente de versiones y restauración ficticia |
| RF-005-04/06 | base/index, SRI, T00505/06 | Frontend exacto/hashes, browser carga/gráfico/menú/móvil/CDN caído; checks/61 HTML/build idéntico |
| RF-006-01/02 | cargos_asignables/UserRegistrationMixin/form/processor, T00601/02/04 | Matriz 35 POSTs/cargos IDs arbitrarios, root con/sin cargo, revocación GET→POST, menú/UI coherentes, anónimo/inactivo/CSRF |
| RF-006-03/04 | views/model/helpers, T00603/04 | Fallos DB/preparación/storage/RuntimeError revierten; foto vieja tras commit, limpieza fallida documentada, sin reprocesar ni fila tras POST inválido |
| RF-006-05 | trece métodos integridad, T00604/05 | Suite total 75 (57 recibidos + 6 dependencias + 13 integridad), check/esquema/browser; aceptación manual pendiente |

Detalles reproducibles: [005](../specs/005-actualizacion-dependencias/validation.md), [006](../specs/006-integridad-registro/validation.md). Evidencia de 001–004 conservada como historial; ninguna suma de asociaciones se presenta como porcentaje de cobertura. Sin migraciones reales/producción/commit/push.
