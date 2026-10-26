# Trazabilidad de requisitos y pruebas

La matriz siguiente es la vista vigente de los requerimientos del informe. Las secciones por spec, más abajo, conservan el detalle y la evidencia histórica.

## Matriz HU/RT/RNF vigente

Actualizada el 2026-10-25 (tras implementar la 013). Estados: **Cubierto** (implementado y probado), **Parcial** (implementado con un límite declarado), **Sin evidencia** (implementado o decidido, sin medición o sin prueba en dispositivo). Pruebas automáticas: Django 210, Edge 22 y Flutter 23 OK en Windows (2026-10-25, rama del paso 3).

| Req. | RF | Prueba / evidencia | Estado y límite |
|---|---|---|---|
| HU-01 Familiar configura plan y medicación | RF-009, RF-010-02/03, RF-013-07 | Suite Django CuidadosApp; `test_web_matrix_by_role`, `test_api_matrix_by_role_without_side_effects` | **Cubierto** en pruebas automáticas (titular y familiar configuran; cuidador 403). Sin prueba en dispositivo |
| HU-02 Cuidador ve agenda diaria | RF-010-03, RF-013-08/14 | `test_lists_include_patients_of_two_titulars`, matriz API (`summary`), `patient_roles_test.dart` | **Cubierto** en pruebas automáticas. Sin prueba en dispositivo |
| HU-03 Cuidador confirma medicamento (auditable) | RF-009, RF-010-03/05, RF-013-09 | `test_caregiver_is_the_author_and_occurrence_is_recorded_once` | **Cubierto**: autor = cuidador y ocurrencia única entre titular y cuidador |
| HU-04 Cuidador registra cambio de posición | RF-010-04, RF-011-02 | `test_start_clock_without_fabricating_care_and_reject_replay`, `clock_panel_test.dart` | **Parcial**: el cuidador registra con autor propio (013); falta prueba en Android físico (T-011-09) |
| HU-05 Familiar recibe push ante riesgo | RF-010-07, RF-011-03, RF-012-07/13/14 | `test_push.py` (push de caída inmediato, reservas fuera de transacción), `test_fall_push_uses_existing_channel_once_and_first`, `test_push_command_sends_fall_to_family_and_caregiver` (Firebase simulado) | **Sin evidencia** real: push inmediato, texto genérico y destinatarios implementados y probados con Firebase simulado; falta Firebase de prueba en un Android físico (D-054) |
| HU-06 Familiar ve historial | RF-010-05, RF-012-06 | `test_edge_fall_is_stored_in_history_with_reception_time` | **Parcial**: delegación y autoría cubiertas (013, `test_revocation_stops_actions_and_keeps_authorship`); la caída aparece como «Indeterminada» en el historial móvil (QA-16) |
| HU-07 Familiar gestiona suscripción en el portal | RF-007, RF-010-06/11 | Suite Django PlanesApp; [validación 007](../specs/007-planes-app/validation.md) | **Parcial**: pagos simulados; ensayo web ↔ app pendiente (T-011-05) |
| RT-01 Postura con MediaPipe | RF-010-09 | `edge.test_posture`, `edge.smoke` en Windows | **Parcial**: pruebas sintéticas; sin ejecución en vivo con cámara |
| RT-02 Inmovilidad por tiempo configurable | RF-010-09 | `test_immobility_once_and_reset_on_gap_or_position`, `test_missing_signal_never_generates_immobility` | **Parcial**: pruebas sintéticas; sin ejecución en vivo |
| RT-03 Caídas | RF-012-01..05, 10..12 | `edge.test_fall`, `edge.test_run` | **Parcial**: pruebas sintéticas; protocolo de caídas sin ejecutar (D-053) |
| RNF sin video a la nube | RF-012-05, contrato de 7 claves de 010 | `test_edge_plan_revocation_dedup_and_no_clinical_event` (rechaza un campo `image` con 400) | **Cubierto** por contrato cerrado y prueba de regresión |
| RNF alerta de caída ≤ 10 s | RF-012-07/08/13 | Sin medición de punta a punta (QA-15) | **Sin evidencia**: el push ya sale al recibir la caída (D-051); falta medir con Firebase real (D-054) |
| RNF inferencia < 100 ms por cuadro | RF-012-08/09 | `edge/bench.py` solo con video sintético sin personas (no válido) | **Sin evidencia**: medir con el video del protocolo |
| RNF caídas ≥ 90 % y FP ≤ 5 % | RF-012-01..03 | Protocolo escrito en [edge/README.md](../edge/README.md) | **Sin evidencia**: protocolo sin ejecutar (D-053) |
| RNF disponibilidad ≥ 99,5 % | — | — | Objetivo de diseño **no medido** (D-060) |

Pendientes que cambian estados: prueba en dispositivo de la [spec 013](../specs/013-cuidado-delegado/validation.md) (HU-01/02/03/04/06), D-051/D-054/D-058 (HU-05 y alerta ≤ 10 s), D-053 (RT-03 y precisión), T-011-05/09 (dispositivo).

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

## PlanesApp — 007, trazabilidad implementada

[Spec](../specs/007-planes-app/spec.md), [plan](../specs/007-planes-app/plan.md), [tareas](../specs/007-planes-app/tasks.md). Filas implementadas y verificadas según [validation.md](../specs/007-planes-app/validation.md): 117 tests OK y navegador con límites. OAuth real/zoom/preferencia reducida/aceptación pendientes. SignupForm real en UsuarioApp/signup_forms.py, nuevas pruebas en PlanesApp/tests.py. Fecha: 2026-10-06.

| RF | Tareas previstas | Diseño / archivos previstos | Prueba propuesta |
|---|---|---|---|
| RF-007-01 | 03/14/16 | UsuarioApp services/adapters/forms y signup | Alta segura/duplicados/rollback/flags/cargo |
| RF-007-02 | 01/05/14/15/16 | Configuración social/adapters/templates | OAuth mock/cancelación/colisión/conexión; ensayo externo si configurado |
| RF-007-03 | 04/05/14/16 | Allauth email y permisos de contratación | Confirmación/expiración/reenvío/gate/MFA preservados |
| RF-007-04 | 02/07/14/15/16 | Plan/beneficios/migraciones/catalogo | Cuatro precios/beneficios/anonimato y plan inactivo |
| RF-007-05 | 02/03/07/12/14/16 | Subscription/services/resumen | Free/propiedad/estado fechas/GET sin escritura |
| RF-007-06 | 02/08/14/15/16 | Métodos/forms/simulator/services | Lista cerrada/no PAN-CVC/fecha/default/IDs ajenos |
| RF-007-07 | 09/15/16 | Componente card.js/CSS de app | Navegador giro/teclado/móvil/reducido/sin JS |
| RF-007-08 | 10/14/15/16 | Operación/services/checkout/resultado | Precio servidor/CSRF/idempotencia/atomicidad/error |
| RF-007-09 | 11/14/15/16 | Servicios/cancelación/resumen | Cambio inmediato/Free/sin cargo rol/cancelar/revocar |
| RF-007-10 | 12/14/15/16 | Fechas/renovación en servicios | Mes corto/bisiesto/DST/rechazo/no doble período |
| RF-007-11 | 02/10/11/12/13/14/16 | Operaciones/snapshots/historial | Histórico estable/paginación/solo titular |
| RF-007-12 | 06/07/14/15/16 | Home/UserListView/processor/nav/selector visual | Matriz por cargo y root/URL/HTML/no consulta cuentas cliente |
| RF-007-13 | 01/02/06/07/09/14/15/16 | Integración/theme/tests/docs | Suite aislada/build/navegador/docs y límites |

Sustituciones autorizadas explícitas: cierre RF-001-02 y tests asociados de 005; acceso lector Home/Usuarios y verificación none conservados antes. Apertura actual verificada en 007; evidencia histórica del cierre permanece identificada como tal. Registro y gestión 004/006 continúan vigentes. Tareas referidas como 03 representan T-007-03, etc.

## 008 — Dashboard y navegación, propuesta documental 2026-10-06

[Spec](../specs/008-dashboard-navegacion/spec.md), [plan](../specs/008-dashboard-navegacion/plan.md), [tareas](../specs/008-dashboard-navegacion/tasks.md). Ningún RF implementado/verificado funcionalmente en esta fase; todas las tareas pendientes de autorización posterior.

| RF | Tareas T-008 | Archivos previstos | Evidencia propuesta |
|---|---|---|---|
| RF-008-01 | 01/05/06/07 | nav.html compartido | Seis SVG, labels, escritorio/móvil |
| RF-008-02 | 01/05/06/07 | nav/processor/Home | Matriz, guard previo, URL y menú coherentes |
| RF-008-03 | 03/04/05/06/07 | dashboard.py propuesto, Home/index/grafico_home | Datos reales del prototipo, cero, HTML sin JS/CDN |
| RF-008-04 | 03/04/05/07 | dashboard.py, modelos/services como referencia | Fechas/cancelación/población/snapshots y no escritura GET |
| RF-008-05 | 02/05/06/07 | visual_mode.html propuesto, index/mi_suscripcion | Mismos SVG, POST/CSRF/preferencia propia y sin JS |
| RF-008-06 | 02/04/05/06/07 | templates/estilos/JS existentes | Suite aislada/build/cinco anchos/modos/teclado/fallback |

### Ejecución posterior de 008 — 2026-10-06

Las filas de propuesta anteriores conservan el diseño inicial. Alcance completo autorizado posteriormente e implementado; T-008-01–07 técnicas completas, aceptación y zoom/preferencia reducida nativos pendientes. [Validación](../specs/008-dashboard-navegacion/validation.md), [evidencia servidor](../specs/008-dashboard-navegacion/evidencia/verificacion.json) y [navegador](../specs/008-dashboard-navegacion/evidencia/navegador.json).

| RF | Implementación real | Evidencia |
|---|---|---|
| 01/02 | nav.html y guard/flag vigentes | Matriz de diez casos y variantes en homeApp/test_dashboard.py; SVG y clientes/operadores en navegador |
| 03/04 | PlanesApp/dashboard.py, Home/index/grafico_home.js | Clasificación comparada con summary, límites/cancelación/volumen/snapshots, cuatro consultas, JSON escapado y vacío |
| 05 | components/visual_mode.html en Home/Mi suscripción | Preferencia/POST/CSRF y SVG compartido; cambios de modo en navegador, incluso sin recursos JS |
| 06 | Estilos/cache/versiones, base extendida details/noscript | 127 tests OK, 77 HTML/build y cinco anchos/dos modos/fallback/teclado; 18 capturas, límites manuales declarados |

Pruebas nuevas en homeApp/test_dashboard.py; dos expectativas antiguas de tests.py actualizadas porque el gráfico demostrativo fue sustituido expresamente en 008. Evidencia 007 no se presenta como validación de estas nuevas reglas.

## 009 — CuidadosApp, antecedente documental 2026-10-06

[Spec](../specs/009-cuidados-cuidadores/spec.md), [plan](../specs/009-cuidados-cuidadores/plan.md), [tareas](../specs/009-cuidados-cuidadores/tasks.md). Doce RF/trece tareas pendientes, ninguna implementación ni evidencia funcional todavía. Los archivos nuevos siguientes son previstos, no existentes. P-009-01/02/03 confirmadas; D-037–041 distinguen requisitos humanos de precisiones técnicas.

| RF | Tareas T-009 | Integración / archivos previstos | Verificación posterior propuesta |
|---|---|---|---|
| RF-009-01 | 01/04/06/10/11/13 | CuidadosApp permissions/views/querysets, nav/Home | Titular en todos los cargos/root/sin perfil, IDs anidados/avisos ajenos 404 |
| RF-009-02 | 03/05/11/13 | PlanesApp models/nueva migración/catálogo/dashboard | Tres precios/cupos; Pro/Hogar histórico, snapshots y sin cobro nuevo |
| RF-009-03 | 02/04/05/11/13 | CuidadosApp Patient/forms/services | Alta/archivo/reactivación, validación y último cupo concurrente |
| RF-009-04 | 02/06/11/13 | Medication/MedicationTime/events/agenda | Horarios/dosis ingresada, omitida/realizada y no doble registro |
| RF-009-05 | 02/07/10/12/13 | CareGuide/templates/static SVG | Fuente/alt/texto/ilustración coherentes, sin análisis IA |
| RF-009-06 | 02/08/11/12/13 | PositionTimer/CareEvent/services/JS | 60/90/120, recarga/pausa/cambio/generación e instante servidor |
| RF-009-07 | 02/09/11/12/13 | ReminderReceipt/agenda/POST acuse/JS | Preaviso/vencimiento/dedup pestañas, suspensión/retorno; leer no realiza |
| RF-009-08 | 02/06/09/10/11/13 | CareTask/events/agenda/templates | Propios, horarios/pendientes y estados manuales |
| RF-009-09 | 02/06/08/10/11/13 | CareEvent/snapshots/history | Edición conserva histórico, corrección vinculada, sin falso cuidado |
| RF-009-10 | 03/04/05/11/12/13 | CapacitySelection/quotas y PlanesApp services/checkout | Selección propia, pago fallido/rollback, fin de período/vencimiento |
| RF-009-11 | 01/07/10/12/13 | CuidadosApp templates, Home/nav/visual_mode/theme @source | Cliente a cuidados, internos preservados, SVG/modos/móvil/teclado/fallback |
| RF-009-12 | 01–13 | core.test_settings, tests/servicios/docs | Suite aislada/regresión, pertenencia/atomicidad/DST, build y navegador real |

Ninguna prueba de 007/008 acredita estos nuevos RF; serán ampliadas tras autorización. No cambios de fuentes ejecutables ni migraciones en DOCUMENTAR.


## 009 — Implementación autorizada y verificada, 2026-10-06

RF-009-11/12 → T-009-15 completa → templates/tailwind/layout/select.html, static/css/styles.css y revisión de CSS en base.html. [Mediciones](../specs/009-cuidados-cuidadores/evidencia/select-navegador.json), [contratos](../specs/009-cuidados-cuidadores/evidencia/select-contratos.json) y [validación](../specs/009-cuidados-cuidadores/validation.md): reproducción 240 px, corrección 20 px, cuatro vistas, teclado/POST/build y regresión completa. Intermitencia previa de carrera SQLite documentada.

Seguimiento visual del mismo día: RF-009-05/11 → T-009-14 completa → CareGuide.illustration, guide.html y cuatro PNG v2. [Validación](../specs/009-cuidados-cuidadores/validation.md) y [mediciones](../specs/009-cuidados-cuidadores/evidencia/imagenes-v2-navegador.json): 31 pruebas del módulo, assets/alt y cuatro vistas 390/1440 claro/oscuro. SVG y evidencia inicial conservados como antecedente; sin migración ni reglas nuevas.

La tabla anterior conserva diseño inicial, no estado vigente. D-042 autoriza alcance completo. T-009-01–11 completas; 12 visual parcial y 13 entrega documental con aceptación pendiente. [Validación](../specs/009-cuidados-cuidadores/validation.md), [servidor](../specs/009-cuidados-cuidadores/evidencia/verificacion.json), [navegador](../specs/009-cuidados-cuidadores/evidencia/navegador.json) y [migraciones](../specs/009-cuidados-cuidadores/evidencia/migraciones.json).

| RF | Archivos reales | Prueba/evidencia efectiva |
|---|---|---|
| 01 | CuidadosApp/permissions.py, services.own_patient, views.CareView, nav | ownership_all_roles_root_and_no_profile, anon/inactive/CSRF/private cache; otra cuenta/404 en navegador |
| 02 | PlanesApp/models.py y migrations/0003–0004, catálogo | legacy_hogar_preserved_and_not_renewable, ensayo catálogo/reversión/snapshots |
| 03 | Patient/forms/services.save_patient y set_patient_active | límites/validación/versiones/owner, archive/reactivation, simultaneous_last_slot_never_exceeds_capacity |
| 04 | Medication/MedicationTime, save_daily/record_daily, scheduling.agenda | horarios múltiples/errores/versiones, omission/snapshots/duplicate; edición no reabre dosis, fecha efectiva |
| 05 | CareGuide, migration/0002, cuatro SVG/guides.html | database_constraints_and_guides_assets, capturas de guías completas y móvil |
| 06 | PostureTimer/CareEvent, services.record_posture/configure_timer, care.js | intervalos/replay/clock y timer_change_pause_resume_and_stale_generation; recarga/pausa en navegador |
| 07 | ReminderReceipt, scheduling.reminders/claim_reminder, care.js/base.html | ten_minutes_due_claim_and_new_generation, foreign_reminder_claim; dos pestañas/recarga/preaviso/vencido |
| 08 | CareTask/agenda, task/event views y templates | tasks_manual_daily_ranges_and_omission, DST/medianoche y filtro inválido 404 |
| 09 | CareEvent, record_daily/correct_event, history.html | snapshots/correction_preserves_original_and_timer; historial/autor y corrección con formulario sin scripts |
| 10 | capacity.py, CapacitySelection y PlanesApp execute/forms/views | reducción/pago fallido, cancelación/selection/resume, vencimiento/rollback/último método; flujo Free en navegador |
| 11 | Home/nav/Layout, CuidadosApp templates/static, theme @source | regresión Home/Planes, cinco anchos/dos modos, keyboard Tab y fallback; Inicio interno conserva agregados |
| 12 | CuidadosApp/tests.py/core.test_settings y evidencia | 31 tests nuevos/158 totales, ensayo migración/carrera SQLite, check/esquema/89 HTML/JS/Ruff/Tailwind/13 JPEG; límites manuales declarados |


## 010 — Aplicación móvil, trazabilidad prevista 2026-10-19

[Spec](../specs/010-aplicacion-movil/spec.md), [plan](../specs/010-aplicacion-movil/plan.md), [tareas](../specs/010-aplicacion-movil/tasks.md). Propuesta, sin implementación ni pruebas ejecutadas.

| RF-010 | Fuente | Tareas T-010 | Evidencia posterior prevista |
|---|---|---|---|
| 01 | Cuentas 007 y acceso móvil del informe | 01–04,11–12 | Autenticación/MFA/Google/revocación |
| 02 | Pacientes 009 y alcance del informe | 01–02,05,07,11–12 | Propiedad/cupos/roles/IDs ajenos |
| 03 | HU-01/02/03 | 01–02,06–07,11–12 | Agenda/medicación/duplicidad y concurrencia |
| 04 | HU-04 y guías 009 | 01–02,06–07,11–12 | Reloj, versiones y guía Android |
| 05 | HU-06 | 01–02,06–07,11–12 | Autor/snapshot/correcciones/privacidad |
| 06 | HU-07 | 01–02,05,07,11–12 | Plan y portal comercial existente |
| 07 | HU-05 | 01–02,09,11–12 | Dispositivo real, permisos/logout/privacidad |
| 08 | Familiar/cuidador del informe; pendiente | 01–02,08,11–12 | Permisos por vínculo y revocación |
| 09 | RT-01/02/03, RNF-01; etapa pendiente | 01–02,10–12 | Evento real/sintético distinguido, autenticación nodo |
| 10 | Integridad 009 y cliente móvil propuesto | 01–03,06–07,11–12 | Red perdida/reintentos/conflictos sin doble registro |


## Ajuste 010 — iOS/Android, funciones por plan y MediaPipe, 2026-10-19

Sustituye la condición opcional anterior para detección de posición; colaboración sigue pendiente. Toda la evidencia siguiente es prevista, no ejecutada.

| RF | Fuente | Tareas | Validación propuesta |
|---|---|---|---|
| RF-010-09 | Aclaración humana MediaPipe, D-048 | T-010-10/14/15/11/12 | Detector real, clasificación/lateralidad/indeterminada, nodo autorizado y capacidad vigente |
| RF-010-11 | Aclaración humana funciones por plan, D-049 | T-010-01/02/13/15/11/12 | Matriz Free/Plus/Premium, petición API directa, expiración, reducción, cola de avisos e historial |
| RF-010-12 | Aclaración humana iOS/Android, D-047 | T-010-03/15/11/12 | Evidencia independiente en ambos SO, permisos, sesión y paridad funcional |

RF-010-01–08/10 también requieren comprobarse en ambas plataformas. Matriz propuesta en spec; no modifica por sí sola catálogo, precios, planes históricos ni autorizaciones de código.


## Aplicación móvil — actualización 2026-10-19

010 RF01: allauth+api/base y test_mobile; RF02–06/10: api/views y Flutter care, servicios existentes; RF07: devices/worker, entrega externa pendiente; RF08: no implementado; RF09: api/detection+edge, pruebas sintéticas y modelo, cámara pendiente; RF11: entitlements/API/tests; RF12: plataformas generadas, ejecución nativa pendiente. [Evidencia y límites](../specs/010-aplicacion-movil/validation.md).


### Referencia AI Studio revisada — 2026-10-20

Acceso resuelto y prototipo inspeccionado. Usuario confirma planes de la web (Free/Plus/Premium,1/3/ilimitados) y MediaPipe tanto en teléfono como en nodo fijo. Registro web/login móvil compartidos. [Mapa y límites](../specs/010-aplicacion-movil/referencia-ai-studio.md); spec/plan/tasks010 ampliados, tareas18–23 pendientes. No se afirma que el diseño o la cámara móvil ya estén implementados.


### Código adaptado a referencia — 2026-10-20

Autorización posterior recibida; UI de seis secciones, tema índigo y cámara puntual móvil mediante plugin MediaPipe Android/iOS escritos, manteniendo nodo fijo y planes web. API dual/migración0005 y170 tests aislados OK. Compilación, lock actualizado, UI y cámara reales pendientes por SDK ausente/disco lleno. APK antiguo no contiene estos cambios. [Validación detallada](../specs/010-aplicacion-movil/validation.md).

## Evolución011 — DOCUMENTAR22/10/2026

RF-011-01→T09/10 instalación;02→T01/02 reloj (relacionado RF-010-04/10);03→T03/04 alarmas (RF-010-07);04→T05 integración007/010;05→T06 estilo002/010;06→T07/08 organización. T11 valida conjunto. Todas pendientes, sin evidencia nueva de ejecución. [Spec/aceptación](../specs/011-ecosistema-instalable/spec.md).

## 012 — Detección de caídas (RT-03), 2026-10-22

| RF | Tareas | Código real | Evidencia ejecutada / límite |
|---|---|---|---|
| RF-012-01..04 | T-012-01/02 | `edge/fall.py` | `edge.test_fall` (caída, recuperación, oclusión, suelo, cada condición, config). Sintético |
| RF-012-05 | T-012-04/12 | `edge/run.py` | `edge.test_run` (entrega, reintento, mismo `event_id`); ejecución en vivo pendiente |
| RF-012-11/12 | T-012-10/12 | `edge/run.py` (`Uplink`, `Monitor`), `api/detection.py` | `edge.test_run` (red lenta 2,5/5 s, caída y recuperación, expiración, 403/400); `test_late_risk_is_accepted_but_ordinary_observations_expire` |
| RF-012-06 | T-012-06/08 | `mobile_models.py`, `0007`, `api/detection.py`, `patient_screen.dart` | `test_edge_fall_is_stored_in_history_with_reception_time`; flutter analyze |
| RF-012-07 | T-012-07/11 | `send_mobile_reminders.py` | `test_fall_push_uses_existing_channel_once_and_first`, `test_late_or_failed_risk_push_is_retried_until_delivered_once`, `test_risk_older_than_push_window_is_not_announced` (Firebase simulado) |
| RF-012-08 | T-012-03/06 | `edge/metrics.py`, `run.py`, `detection.py` | `MetricsTests`; log del backend probado; log en vivo pendiente |
| RF-012-09 | T-012-05 | `edge/bench.py` | Ejecutado con video sintético sin personas; KPI no medido |
| RF-012-10 | T-012-02 | `edge/test_fall.py` | Sentarse, sentadilla, inclinarse, cama lento/rápido sin alerta. Sintético |

RT-03 → RF-012-01..05; HU-05 → RF-012-07; HU-06 → RF-012-06. Los RNF de caídas (≥ 90 % / ≤ 5 %, ≤ 10 s, < 100 ms) siguen sin medir: protocolo en [edge/README.md](../edge/README.md#protocolo-de-prueba-20-caídas-simuladas).

## 013 — Cuidado delegado, trazabilidad prevista 2026-10-25

[Spec](../specs/013-cuidado-delegado/spec.md), [plan](../specs/013-cuidado-delegado/plan.md), [tareas](../specs/013-cuidado-delegado/tasks.md). Propuesta: sin implementación ni pruebas ejecutadas.

| Requerimiento | RF-013 | Tareas T-013 | Evidencia prevista |
|---|---|---|---|
| HU-01 (familiar configura) | 07, 09 | 02–04, 07 | Matriz por rol: titular y familiar configuran; cuidador recibe 403 |
| HU-02 (cuidador ve agenda) | 08, 14 | 04, 07, 10 | Agenda con pacientes de dos titulares; vista resumida del cuidador |
| HU-03 (confirmación auditable) | 09 | 03 | `CareEvent.author` = cuidador; ocurrencia única entre titular y cuidador |
| HU-04 (cambio de posición) | 09 | 03, 10 | Postura y reloj registrados por el cuidador con autor propio |
| HU-05 (push al familiar) | 11 | 09 | Riesgo a titular, familiar y cuidador (D-063); cuidado pendiente a titular y cuidador |
| HU-06 (historial y trazabilidad) | 06, 07, 14 | 04, 05, 07 | Historial con autoría que se conserva tras la revocación; cuidador sin historial completo |
| Acceso por invitación (D-050) | 01–06, 10, 13 | 01, 05, 06, 07, 10 | Código de un solo uso, vencido, propio, duplicado, límite de intentos, cupos sin cambio |
| QA-2026-10-22-04 / 08 | 07 | 07, 08 | 404 para ajenos en todos los endpoints con paciente, incluida la detección |

### 013 — Evidencia ejecutada, 2026-10-25

Todas las filas de la tabla anterior tienen prueba automática en `web/CuidadosApp/test_access.py` (21 pruebas) y `mobile/test/patient_roles_test.dart` (3). Detalle por RF en [validation.md](../specs/013-cuidado-delegado/validation.md). Pendiente: navegador y Android físico.

## 014 — Privacidad, trazabilidad prevista 2026-10-25

[Spec](../specs/014-privacidad/spec.md), [plan](../specs/014-privacidad/plan.md), [tareas](../specs/014-privacidad/tasks.md). Propuesta: sin implementación ni pruebas ejecutadas.

| Fuente | RF-014 | Tareas T-014 | Evidencia prevista |
|---|---|---|---|
| QA-2026-10-22-05 / D-052: consentimiento | 01–07 | 01–04, 09 | Política versionada, aceptación en registro y puerta, consentimiento del paciente por alcance, bloqueos y revocación |
| D-052: conservación y purga | 08 | 08 | Purga solo de lo vencido, `--dry-run`, salida sin datos personales |
| D-052: exportación | 09–10 | 05 | JSON sin secretos; 403 para familiar y cuidador en el paciente |
| D-052: eliminación | 11–12 | 06, 07 | Sin filas remanentes; autor «Cuenta eliminada»; sin acceso ni avisos |
| Trazabilidad de operaciones | 13 | 05–07 | `PrivacyOperation` sin identificadores |
| RNF «sin video a la nube» | — | 04 | Se preserva; la detección exige consentimiento propio |

### 014 — Evidencia ejecutada, 2026-10-25

RF-014-01..13 con prueba automática en `web/PrivacidadApp/tests.py` (16 pruebas, reglas activadas) y RF-014-14 en `mobile/test/privacy_test.dart` (4). Detalle en [validation.md](../specs/014-privacidad/validation.md). QA-2026-10-22-05 pasa de «sin spec» a implementado en el prototipo, sin revisión legal ni cifrado en reposo.

## 015 — Integración de `vigia-unificado` e iOS, trazabilidad prevista 2026-10-26

[Spec](../specs/015-integracion-unificado/spec.md), [plan](../specs/015-integracion-unificado/plan.md), [tareas](../specs/015-integracion-unificado/tasks.md). Propuesta: sin implementación ni pruebas ejecutadas.

| Fuente | RF-015 | Tareas T-015 | Evidencia prevista |
|---|---|---|---|
| Comparación con `vigia-unificado`: método y no regresión de 011–014 | 01 | 01, 07 | Las tres suites; `git diff` sin archivos de la lista B |
| Rediseño de la app (HU-02, HU-04, HU-06 en la interfaz) | 02 | 04, 07 | Pruebas de rol y privacidad; Android físico |
| HU-07: plan en la app, cambio en la web | 03–04 | 02, 03 | Prueba del catálogo (Django) y del panel (Flutter) |
| Demo instalable | 05, 07 | 05, 12 | Página con y sin APK; guía sin datos sensibles |
| Marca VIGIA | 06 | 06 | Navegador claro/oscuro |
| D-068: iOS en el alcance | 08–13 | 08–12 | Build de simulador, iPhone físico, avisos, cámara y push según P-015-01 |
| RNF «sin video a la nube» en iOS | 12 | 10 | Observación `platform: "ios"` sin imagen |
