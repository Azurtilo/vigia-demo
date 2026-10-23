# Especificaciones por módulo o cambio

La base original no trae un módulo de negocio predefinido; esta copia añade PlanesApp solicitado en 007. **NuevaAPP es un ejemplo de nombre**, no una tarea pendiente ni una app a crear automáticamente.

## Índice

| Número | Módulo / cambio | Ruta | Estado | Código autorizado |
|---|---|---|---|---|
| 001 | CalidadBase: seguridad, pruebas y configuración | [001-calidad-seguridad-base](./001-calidad-seguridad-base/) | Verificado técnicamente; aceptación funcional pendiente | Sí; implementado 2026-09-20 |
| 002 | Renovación visual de Base-2 | [002-renovacion-visual](./002-renovacion-visual/spec.md) | Implementada; regresión OK, revisión visual parcial y aceptación pendientes | Sí; alcance completo autorizado y ejecutado 2026-10-02 |
| 003 | Modo claro/oscuro por usuario | [003-modo-visual-usuario](./003-modo-visual-usuario/spec.md) | Implementado; 43 tests OK; T-003-07 visual parcial y T-003-08 revisión del propietario pendientes | Sí; alcance completo autorizado por instrucción posterior el 2026-10-02; migración real excluida |
| 004 | UsuarioApp: restablecimiento administrativo y jerarquía de cuentas | [004-administracion-usuarios](./004-administracion-usuarios/spec.md) | Implementado; 57 tests OK; T-004-07 envío válido por UI y T-004-08 revisión pendientes | Sí; alcance completo autorizado y ejecutado por instrucción posterior el 2026-10-02; sin migraciones nuevas/reales |
| 005 | Actualización segura de dependencias Python/JavaScript | [005-actualizacion-dependencias](./005-actualizacion-dependencias/spec.md) | Implementada/verificada: lock de 52 paquetes, SRI, migraciones ficticias; aceptación pendiente | Sí; correcciones autorizadas posteriormente el 2026-10-02 |
| 006 | Permisos e integridad de Registro/Perfil | [006-integridad-registro](./006-integridad-registro/spec.md) | Implementada/verificada: cargos y atomicidad/fotos; aceptación pendiente | Sí; regla y alcance confirmados por instrucciones posteriores |
| 007 | PlanesApp: registro público local/Google y suscripciones simuladas | [007-planes-app](./007-planes-app/spec.md) | Implementada; 117 tests OK, visual con límites, OAuth real/aceptación pendientes | **Sí; alcance completo autorizado posteriormente el 2026-10-06, sin migración real** |
| 008 | Dashboard de suscripciones y navegación coherente | [008-dashboard-navegacion](./008-dashboard-navegacion/spec.md) | Implementada; 127 tests OK, navegador y aceptación con pendientes manuales | Sí; alcance completo autorizado posteriormente el 2026-10-06 |
| 009 | CuidadosApp: pacientes, medicamentos y cuidados por cuidador | [009-cuidados-cuidadores](./009-cuidados-cuidadores/spec.md) | Implementada; 158 tests OK, navegador verificado con límites; revisión manual/aceptación pendientes | Sí; alcance completo autorizado posteriormente el 2026-10-06, sin migración real |
| 010 | Aplicación móvil VIGIA: Flutter iOS/Android, funciones por plan y MediaPipe | [010-aplicacion-movil](./010-aplicacion-movil/spec.md) | Demo implementada; APK Android, integración de nodo y pruebas; pendientes nativos/externos en validation.md | Sí, instrucción posterior 2026-10-19 |
| 011 | Ecosistema instalable: reloj, avisos locales, estilo web y separación web/mobile/edge | [011-ecosistema-instalable](./011-ecosistema-instalable/spec.md) | En implementación: T01/02/07/08 hechas; T03/04/06/09 parciales; T05/11 pendientes; T10 (iOS) fuera de alcance por [D-011-02](../docs/DECISIONES.md). Windows 2026-10-22: 176 Django, 19 Flutter y 5 Edge OK; [validación](./011-ecosistema-instalable/validation.md). Falta notificación y APK en un Android real; aceptación pendiente. [Tareas](./011-ecosistema-instalable/tasks.md) | Sí, «perfecto ahora modificalo» 2026-10-22; sin producción, tiendas ni migración real. **Android primero, iOS fuera de alcance** |

Siguiente número sugerido: 012. Comprobar el siguiente libre en cada uso. Una app puede tener varias specs de evolución; una spec transversal puede afectar varias apps.

Auditoría independiente y cierre de correcciones: [VALIDACION_PREPRODUCCION.md](../docs/VALIDACION_PREPRODUCCION.md), 2026-10-02. La auditoría inicial detectó bloqueadores; la implementación posterior autorizada de 005/006 los corrigió en el alcance verificado. Conserva pendientes operativos y de revisión manual; no equivale a aceptación ni autorización para producción.

## Organización

Una solicitud de nuevo módulo crea una carpeta `specs/001-nueva-app/` —ejemplo de ruta, solo después de recibir un pedido concreto— con:

| Archivo | Propósito | Momento |
|---|---|---|
| spec.md | Qué debe hacer, reglas, permisos y aceptación | Primero |
| plan.md | Cómo se propone integrarlo en el código real | Después de la spec |
| tasks.md | Pasos, dependencias y criterios de terminado | Después del plan |
| validation.md | Evidencia real y pendientes | Al validar; no simular resultados en DOCUMENTAR |

Plantillas: [spec](./_templates/spec.md), [plan](./_templates/plan.md), [tasks](./_templates/tasks.md), [validation](./_templates/validation.md).

## Estados y permisos de trabajo

Borrador documental → listo para revisión → aprobado para implementar tareas indicadas → en implementación → verificado técnicamente → aceptado por usuario.

La aprobación necesita evidencia del mensaje del usuario; no se deduce de que existan los tres archivos. Si hay decisiones críticas pendientes, se mantiene borrador o listo para revisión con bloqueo explícito.

## Identificadores

Usar IDs estables por spec, por ejemplo RF-001-01 y T-001-01. Relacionarlos con aceptación y pruebas en [TRAZABILIDAD](../docs/TRAZABILIDAD.md). Un criterio no debe limitarse a «funciona bien».

Un cambio pequeño conserva carpeta y RF, actualiza requisitos vigentes y añade una sección fechada de tareas. Una regla sustituida queda registrada en decisiones; no reciclar un ID para otro significado.

Una spec nueva no autoriza automáticamente implementar ni despliega cambios de una spec anterior.

## Evolución22/10/2026

[011 — Ecosistema instalable, reloj y organización](011-ecosistema-instalable/spec.md): documentada el 22/10/2026 e implementación autorizada después (ver fila del índice). iOS fuera de alcance desde 2026-10-22. Siguiente número libre sugerido 012; verificar.
