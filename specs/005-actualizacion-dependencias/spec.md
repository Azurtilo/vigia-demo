# 005 — Actualización segura de dependencias de la base

Fecha: 2026-10-02. Estado: **implementación autorizada; P-005-01 confirmada**.
Implementación autorizada: **SÍ**, instrucción posterior del propietario: «te autorizo a aplicar las correcciones de la validación». También confirmó conservar axes/preventconcurrentlogins comentados y opcionales. La fase de auditoría está cerrada; las correcciones constituyen una fase separada. P-005-01 confirmada posteriormente: «Sí, incluirlos y verificar colisiones y recuperación por respaldo». Solo datos ficticios, sin migrar la base real.

## Necesidad y resultado

El propietario reutiliza esta base en sus proyectos futuros y necesita corregir dependencias antiguas/vulnerables, conservar las capacidades actuales y reducir la distancia entre actualizaciones. La [auditoría global](../../docs/VALIDACION_PREPRODUCCION.md) identifica Django 5.1 sin soporte y avisos asociados a otras versiones Python/JavaScript. El objetivo es una instalación reproducible con versiones mantenidas y flujos de 001–004 preservados.

## Alcance

Actualizar las dependencias Python declaradas que lo requieran por seguridad, soporte o compatibilidad, explicando las que se conservan. Incluir bibliotecas necesarias para hashers configurados y MFA actual; registrar transitivas y artefactos verificables. Adaptar solo ajustes/importaciones/formularios/plantillas/pruebas afectados por esas actualizaciones. Fijar y actualizar scripts CDN con verificación de integridad. Documentar instalación limpia y mantenimiento recurrente como procedimiento manual.

Reutilizar UsuarioApp/homeApp/theme/core; no crear una app ni reconstruir autenticación, usuarios, navegación o tema. Se propone Django **5.2 LTS** en su parche vigente (candidata consultada **5.2.17**), con Python **3.12.x** mantenido. Las demás candidatas están en el [inventario](../../docs/evidencia/auditoria-20261002/INVENTARIO_DEPENDENCIAS.md); resolver versiones no acredita ejecución funcional.

Fuera de alcance: corregir asignación de cargos en Registro (AUD-004), transacciones/fotos/perfil (AUD-005), nuevos permisos globales, MFA obligatorio/SSO/passkeys, cifrado o rotación de semillas existentes, nuevo módulo de auditoría, nuevas protecciones antiabuso, cambiar motor DB, activar axes/concurrentlogins, configurar SMTP, rediseño visual, Node.js, automatizaciones programadas, productos derivados ya existentes, datos reales, producción, despliegue, commits/push o migraciones sobre bases existentes. Esos hallazgos no se consideran solucionados al actualizar librerías.

## Actores, permisos y datos

Este alcance de dependencias no concede ni revoca facultades funcionales. El contrato de Registro de 001 fue sustituido posteriormente por 006 con autorización propia; el helper global se conserva. Se mantiene la política específica de 004: cargo requerido incluso al superusuario para activar/desactivar/restablecer, ADMIN sobre inferiores y MANAGER solo RESTRICTED para estado. Mantener propiedad exclusiva de preferencia visual de 003 y registro público cerrado.

La matriz completa de anónimo/inactivo/sin perfil/sin cargo/código desconocido/RESTRICTED/MANAGER/ADMIN/staff/superusuario se conserva por acción según las specs vigentes; no unificar silenciosamente sus excepciones. No editar hashes, MFA, cargos, preferencias o fotos para hacer pasar pruebas. Cambios de datos impuestos por allauth quedan sujetos a **P-005-01**, no a una autorización implícita.

## Requisitos

- **RF-005-01 — Versiones mantenidas.** Instalar un parche vigente de Django 5.2 LTS y versiones compatibles de los demás paquetes, sin prereleases. Revisar todos los pins existentes y las transitivas resultantes; registrar avisos y condiciones, sin sustituir la revisión por instalar automáticamente «latest».
- **RF-005-02 — Autenticación compatible.** Preservar login por usuario/email, cierre público, registro/perfil actuales, recuperación propia/por correo, reconfirmación administrativa, MFA TOTP/recuperación, sesiones y permisos 001–004. Actualizar settings/importaciones/templates allauth solo para mantener ese comportamiento. Completar bibliotecas de los hashers normales configurados, incluido bcrypt; Argon2 continúa primero, MD5 exclusivamente en pruebas. No habilitar nuevas formas de MFA/SSO al instalar extras.
- **RF-005-03 — Migraciones controladas.** Identificar y ensayar cambios de esquema/datos de terceros en bases sintéticas nuevas y con estado equivalente a la versión anterior. Detectar colisiones de correos y estados inconsistentes antes del paso afectado. Registrar operaciones irreversibles y recuperación por respaldo. No aplicar migraciones reales. Si un efecto nuevo excede P-005-01, detener la tarea afectada antes de asumirlo.
- **RF-005-04 — JavaScript reproducible.** Sustituir Alpine flotante, DOMPurify antiguo y ECharts afectado por versiones exactas verificadas; añadir SRI/crossorigin coherentes con los bytes servidos, o artefactos locales con origen/hash/licencia documentados. Mantener menús, diálogos, notificaciones y gráfico en ambos modos, además de su degradación ante fallo de CDN. Sin incorporar Node.js.
- **RF-005-05 — Instalación y mantenimiento.** Declarar entradas de dependencias, distinguir uso de aplicación/herramientas/opcionales y mantener un lock completo con hashes regenerado en aislamiento. Conservar un comando de instalación documentado y las capacidades opcionales declaradas/desactivadas de D-008. Probar instalación limpia y pip check sin paquetes globales; documentar recreación del venv roto sin eliminar el previo antes de validar. Proponer revisión manual mensual de avisos y trimestral de versiones, con remediación prioritaria de avisos alcanzables y actualización antes del fin de soporte.
- **RF-005-06 — Evidencia y regresión.** Ejecutar suite completa, regresiones pertinentes de compatibilidad/migración/hashing, check/esquema, deploy simulado, build, pruebas de UI y auditoría de dependencias resueltas. No omitir/relajar permisos, CSRF, TOTP, sesiones o rollback para obtener verde. Registrar lo ejecutado por requisito, pendientes y límites; actualizar estado y trazabilidad. Reauditar bloqueadores sin cerrar hallazgos ajenos a esta spec.

## Aceptación y requisitos no funcionales

| RF | Criterio verificable |
|---|---|
| 01 | Instalación en entorno limpio, Django 5.2 con soporte y versiones exactas documentadas; consulta de avisos cubre conjunto instalado y transitivas, sin bloqueadores de dependencia sin resolver |
| 02 | Suite de 001–004 y casos nuevos pertinentes pasan, incluido login/MFA/sesiones con hashes normales sintéticos; cargo/estado y configuración visual intactos |
| 03 | Migraciones nuevas/datos existentes sintéticos comprobados; casos de duplicados/colisiones y recuperación documentados; P-005-01 confirmada antes del cambio; cero acceso a datos reales |
| 04 | No URL de versión flotante; origen e integridad de cada script externo verificados; navegador claro/oscuro y fallo de CDN sin perder acciones esenciales |
| 05 | Lock reproducible, instalación/check sin globales, procedimiento de venv y revisión periódica utilizable; herramientas/opcionales no se activan como funcionalidad |
| 06 | Comandos/resultados, regresiones, navegador y pendientes honestos asociados al código entregado; informe global conserva hallazgos de Registro/integridad pendientes |

Mantener idioma es-cl, zona America/Santiago, layouts/bloques/tokens y Tailwind standalone 4.3.0. La seguridad no se define como ausencia eterna de CVEs: cada revisión registra fecha, origen y alcance. No instalar herramientas globales ni usar pip freeze de un entorno ajeno. Cero secretos/credenciales reales en evidencia.

## Decisión crítica confirmada

**P-005-01 — Efectos de migración allauth.** La candidata 65.19.7 añade account.0006–0009 y mfa.0003: correos de User/EmailAddress en minúsculas, desmarcado de correos principales adicionales, cambios de índice/campo y unicidad de principal/tipos MFA. Los backfills tienen reversión noop; rollback de código no recupera los valores previos. [Evidencia](../../docs/evidencia/auditoria-20261002/migraciones-allauth.json).

Confirmados expresamente por el propietario el 2026-10-02, después de consultar efectos concretos: incluirlos y verificar colisiones/restauración por respaldo. La ausencia de datos reales impide afirmar que no haya colisiones en una copia existente. No se autoriza aplicar migraciones reales.

No hay preguntas pendientes sobre P-004-01/02: fueron confirmadas y no se repiten. La política futura de cargos asignables pertenece a otro alcance; no bloquea documentar 005, pero impide considerar resuelto AUD-004.

## Revisión

2026-10-02: auditoría ejecutada y spec creada primero, antes de plan/tasks. Se propone el siguiente número libre comprobado, 005. Sin cambios de dependencias/código/pruebas versionadas. Revisión y autorización de implementación pendientes.

## Cierre de implementación posterior

2026-10-02: 005 autorizada posteriormente, P-005-01 confirmada, tareas técnicas ejecutadas con 76 tests junto a 006. Lock de 52 paquetes/SRI, compatibilidad/MFA y preflight/migración/restauración ficticias. [Validación](validation.md). La fase DOCUMENTAR anterior queda como antecedente; no hay aceptación funcional ni autorización de DB real/producción. AUD-004/005 fueron corregidos por 006 con autorización propia, no por inferencia del alcance de 005.
