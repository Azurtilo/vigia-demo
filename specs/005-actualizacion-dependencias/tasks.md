# Tareas — 005 / Dependencias

Fecha: 2026-10-02. Implementación autorizada posteriormente y P-005-01 confirmada. Tareas técnicas ejecutadas, evidencia en [validation.md](validation.md); aceptación del propietario pendiente. La auditoría original se conserva como antecedente.

- [x] **T-005-01 — Preparar actualización aislada y preservar cambios.** RF-005-01/05/06. Dependencias: autorización posterior de 005. Fin: estado/diff/manifiesto de fuentes y recuperación sin secretos; intérprete mantenido y nuevo entorno propio preparado, anterior conservado.
- [x] **T-005-02 — Resolver contrato y ensayos de migración.** RF-005-02/03. Dependencias: T-005-01 y confirmación expresa P-005-01. Fin: notas incompatibles/operaciones inventariadas, fixtures sintéticas y recuperación definidas; sin supuestos sobre colisiones ni aceptación de datos reales.
- [x] **T-005-03 — Resolver y fijar dependencias Python.** RF-005-01/02/05. Dependencias: T-005-02. Fin: entradas documentadas, lock/hash completo, bibliotecas de hashers/MFA resueltas, opcionales conservados/desactivados, instalación limpia/pip check y auditoría de transitivas sin bloqueadores de dependencia pendientes.
- [x] **T-005-04 — Adaptar integración de autenticación y verificar migraciones.** RF-005-02/03/06. Dependencias: T-005-03. Fin: settings/API/templates ajustados mínimamente, contratos 001–004 preservados y pruebas pertinentes de datos/constraints/recuperación/hashers/MFA; no cambios de cargos, políticas de negocio ni migraciones reales.
- [x] **T-005-05 — Fijar y actualizar bibliotecas frontend.** RF-005-04/06. Dependencias: T-005-03. Fin: versiones exactas, origen e integridad verificables para scripts externos; interacción/gráfico/fallo de proveedor comprobados sin Node.js ni rediseño.
- [x] **T-005-06 — Ejecutar regresión completa e integración.** RF-005-01 a 06. Dependencias: T-005-04/05. Fin: suite/check/esquema/deploy simulado/build/plantillas y navegador pertinentes con evidencia; resultados vinculados a código/entorno y pendientes manuales explícitos, sin borrar tests para aprobar.
- [x] **T-005-07 — Documentar mantenimiento y entregar revisión.** RF-005-05/06. Dependencias: T-005-06. Fin: guía de instalación/lock/revisión periódica, validation/índices/trazabilidad/estado actualizados; reauditoría de dependencias, AUD-004/005 seguidos por separado en 006; sin aceptación funcional inferida.

## Registro de DOCUMENTAR

2026-10-02: realizada auditoría independiente de la versión actual según skill; informe/evidencia en [VALIDACION_PREPRODUCCION.md](../../docs/VALIDACION_PREPRODUCCION.md). Se crearon spec → plan → tasks para el pedido de corrección de dependencias. Resolución preliminar y consulta de candidatas son evidencia de planificación, no instalación nueva ni ejecución de T-005-03/06. Las 57 pruebas corresponden a versiones antiguas declaradas.

## Autorización y reanudación

Implementación autorizada por instrucción posterior: aplicar correcciones de la validación conservando axes/concurrentlogins comentados. P-005-01 confirmada expresamente: incluir efectos de allauth y verificar colisiones/restauración. AUD-004/005 se documentaron en 006, con regla confirmada y otra instrucción posterior explícita de implementación; no se atribuye su corrección a actualizar librerías.

No migraciones reales, datos reales, producción, despliegues, commit ni push por esta propuesta. Aceptación funcional: pendiente.

## Ejecución realmente realizada

T01: snapshot de 204 archivos seleccionados, entorno anterior conservado y .venv-actualizada sin globales. T02: inspección de cinco migraciones nuevas/tres previas; equivalencia de las previas en Python 3; datos ficticios, preflight, backup y restauración entre versiones comprobados. T03: 49 entradas, 52 paquetes resueltos con hashes; pip-tools 7.6.1 separado, pip 26.2.1 instalado, pip check correcto y consulta de 55 paquetes/versiones Python+JS sin coincidencias.

T04: equivalencia de settings/auth, seis pruebas nuevas de integración incluyendo hashers/migraciones/preflight; MFA en mismo proceso con cascada. T05: tres CDN fijos/SRI, gráfico y degradación navegador. T06: 76 métodos Django correctos, check/esquema/61 HTML/build idéntico; deploy simulado conserva W005/W021 por política de subdominios/preload, sin silenciarlas. T07: guía/estado/decisiones/trazabilidad/informe actualizados. No se realizaron nuevas migraciones propias ni reales.

Ingreso/guardado de credenciales nuevas por interfaz y aceptación funcional siguen pendientes del propietario; esas interacciones están verificadas en servidor, no se declaran realizadas en navegador. Operación/hosting y activación de opcionales requieren su contexto propio.

## Ajuste de T-005-03/07 — 2026-10-02

El propietario detectó requirements.txt con versiones anteriores al regenerarlo. Se confirmó la divergencia frente a requirements.in y .venv-actualizada; se regeneró el lock con el compilador aislado, conservando exactamente las 52 versiones y los hashes de los 52 artefactos previamente verificados. pip check correcto. No cambió código ni versiones instaladas; no se repitió la suite de 76 métodos. [Evidencia de restauración](../../docs/evidencia/actualizacion-20261002/requisitos-restaurados.json). Guía ampliada para distinguir pip freeze, archivo fuente y entorno activo; archivo recibido respaldado, herramientas temporales retiradas.
