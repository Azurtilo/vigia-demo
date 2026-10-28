# Especificaciones por módulo o cambio

VIGIA parte de una base Django reutilizable (001–006) y añade PlanesApp (007), CuidadosApp (009), la app móvil (010–011) y el nodo Edge (010, 012). **NuevaAPP es un ejemplo de nombre**, no una tarea pendiente ni una app a crear automáticamente.

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
| 011 | Ecosistema instalable: reloj, avisos locales, estilo web y separación web/mobile/edge | [011-ecosistema-instalable](./011-ecosistema-instalable/spec.md) | En implementación: T01/02/07/08 hechas; T03/04/06/09 parciales; T05/11 pendientes; T10 (iOS) fuera de alcance por [D-011-02](../docs/DECISIONES.md) hasta el 2026-10-26; vuelve con D-068 en T-015-08..11. Windows 2026-10-22: 176 Django, 19 Flutter y 5 Edge OK; [validación](./011-ecosistema-instalable/validation.md). Falta notificación y APK en un Android real; aceptación pendiente. [Tareas](./011-ecosistema-instalable/tasks.md) | Sí, «perfecto ahora modificalo» 2026-10-22; sin producción, tiendas ni migración real. **Android primero, iOS fuera de alcance** (hasta D-068, 2026-10-26) |
| 012 | Detección de caídas en el nodo Edge (RT-03): regla determinista, riesgo `fall`, aviso push, métricas, bench y protocolo de 20 caídas | [012-deteccion-caidas](./012-deteccion-caidas/spec.md) | Implementada; verificación sintética OK (Django 178, Edge 16, Flutter 19). QA-01/02/03 corregidos (Django 181, Edge 22). Pendientes: ejecución en vivo y protocolo de caídas (D-053); Ajustes del 2026-10-25 (T-012-13..21) implementados en `feature/012-push-inmediato-qa`: push de caída inmediato, recibos fuera de bloqueo, texto genérico, API 26 y QA-09/10/16/19/21. Django 210, Edge 22, Flutter 23 OK. [Validación](./012-deteccion-caidas/validation.md) | Sí, mismo mensaje 2026-10-22; sin producción, migración real ni cámara personal |
| 013 | Cuidado delegado: vínculos familiar/cuidador por código, matriz de permisos por rol, autor real y destinatarios de avisos | [013-cuidado-delegado](./013-cuidado-delegado/spec.md) | Implementada en `feature/013-cuidado-delegado`: T-013-01..10 hechas, T-013-11 parcial. Django 202, Edge 22 y Flutter 22 OK. Navegador revisado por el propietario. Pendiente: Android físico. [Validación](./013-cuidado-delegado/validation.md), [tareas](./013-cuidado-delegado/tasks.md) | Sí, 2026-10-25; sin merge, despliegue ni migración real |
| 014 | Privacidad de datos de salud: política versionada, consentimiento por paciente, plazos y purga, exportación y eliminación de cuenta | [014-privacidad](./014-privacidad/spec.md) | Implementada en `feature/014-privacidad`: T-014-01..09 hechas, T-014-10 parcial. Django 218, Edge 22, Flutter 26 OK. Pendiente: navegador y Android. [Validación](./014-privacidad/validation.md) | Sí, 2026-10-25; sin merge ni migración real |
| 015 | Integración de `vigia-unificado` (rediseño de la app, catálogo de planes en la app, descarga estable del APK, marca web, preparación iOS) e iOS en el alcance (D-068) | [015-integracion-unificado](./015-integracion-unificado/spec.md) | Fusionada en `develop` (PR #8, `8d2be54`): T-015-01..07, T-015-12 y T-015-14 hechas; T-015-13 parcial (marca en navegador y Android físico). Django 235, Edge 22, Flutter 46 OK. Pendiente: iOS (T-015-08..11, Sandra). [Validación](./015-integracion-unificado/validation.md) [Tareas](./015-integracion-unificado/tasks.md) | Sí, T-015-01..07, 2026-10-26; sin merge |
| 016 | Correcciones de la QA del 2026-10-26: Pillow y certifi, herramientas de desarrollo fuera de producción, comando de pruebas con PrivacidadApp, CI mínimo y guía de tareas programadas | [016-correcciones-qa](./016-correcciones-qa/spec.md) | En implementación en `feature/016-correcciones-qa`: T-016-01..03 hechas; CI verde en la [PR #11](https://github.com/Azurtilo/vigia-demo/pull/11). Fusionada en `develop` (PR #11). Pendiente del propietario: programar las tareas en el servidor y decidir la activación del push | Sí, 2026-10-26; sin despliegue |
| 017 | Robustez de la detección de caídas: zona de cama con regla «acostado fuera de la cama», heurísticas contra sábanas y oclusión, avisos de monitoreo ciego (persona no visible, sin imagen, poca luz, nodo sin señal) y guía de instalación. Origen: prototipo `pose_app` | [017-robustez-caidas](./017-robustez-caidas/spec.md) | Fusionada en `develop` ([PR #12](https://github.com/Azurtilo/vigia-demo/pull/12), `2bf9c53`): T-017-01..12, 14 y 15 hechas; T-017-16 (configuración unificada del Edge) en `feature/017-config-caidas`; T-017-13 (pruebas en vivo) pendiente del propietario. Django 247, Edge 56, Flutter 51 OK (sintético). [Validación](./017-robustez-caidas/validation.md), [tareas](./017-robustez-caidas/tasks.md) | Sí, T-017-01..12, 14, 15 y 16 y merge de la PR #12, 2026-10-27; sin migración real ni despliegue |
| 018 | Usabilidad del portal (Django) | En `feature/018-usabilidad-portal`, sin fusionar en `develop` al crear la 019 | Ver esa rama | Ver esa rama |
| 019 | Migración a FastAPI + Firebase: backend y app del proyecto `vigia 26` como base, contrato Edge sin cambios, alertas y push, recordatorios por cron con respaldo local, portal React mínimo y revalidación. `develop` conserva Django como respaldo | [019-migracion-firebase](./019-migracion-firebase/spec.md) | En implementación en `feature/019-migracion-firebase`: T-019-01..06, 08, 09, 12 y 16 hechas: backend completo salvo el despliegue; app con alertas y privacidad (backend 327, reglas 7, Edge 56 y Flutter 92 OK; caída entregada por el cliente real del Edge; push con FCM simulado). Punto de control el 2026-11-04 (D-081). Bloqueos: P-019-03 (cuentas, D-100). [Plan](./019-migracion-firebase/plan.md), [tareas](./019-migracion-firebase/tasks.md) | Sí, T-019-01..15, 2026-10-28; sin merge, despliegue, cuentas reales ni instalación de software |

Siguiente número sugerido: 020. Comprobar el siguiente libre en cada uso. Una app puede tener varias specs de evolución; una spec transversal puede afectar varias apps.

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

## Evolución 22/10/2026

[011 — Ecosistema instalable, reloj y organización](011-ecosistema-instalable/spec.md): documentada el 22/10/2026 e implementación autorizada después (ver fila del índice). iOS fuera de alcance desde 2026-10-22 (vuelve al alcance el 2026-10-26, D-068). [012 — Detección de caídas](012-deteccion-caidas/spec.md) creada e implementada el mismo día. Siguiente número libre sugerido 013; verificar.
