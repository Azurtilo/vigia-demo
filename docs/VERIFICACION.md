# Registro resumido de verificaciones

Este archivo resume verificaciones vigentes de la base. No sustituye la evidencia detallada de cada spec ni debe copiar afirmaciones de otro proyecto sin volver a comprobarlas.

| Fecha | Alcance | Evidencia | Resultado / límite |
|---|---|---|---|
| 2026-09-20 | Entrega documental SDD inicial | [VALIDACION_SDD.md](VALIDACION_SDD.md) | Evidencia histórica del ZIP recibido; sus observaciones previas a la spec 001 no describen el estado actual |
| 2026-09-20 | Spec transversal 001-CalidadBase | [validation.md](../specs/001-calidad-seguridad-base/validation.md) | 15 tests, checks Django, build Tailwind 3 y navegador verificados entonces; aceptación funcional del propietario pendiente |
| 2026-09-22 | Documentación, trazabilidad y migración a Tailwind 4 standalone | [sección fechada de validation.md](../specs/001-calidad-seguridad-base/validation.md#ajuste-del-2026-09-22) | Revisión y resultados del entorno actual; no altera módulos de negocio ni ejecuta ideas del roadmap |
| 2026-10-02 | Implementación autorizada de 002-Renovación visual | [validation.md](../specs/002-renovacion-visual/validation.md) | 27 tests Django, cinco contratos JS, check, sin migraciones, build standalone y contraste OK; navegador con datos sintéticos en cinco anchos y tres paletas. Zoom real/preferencia reducida en navegador y aceptación pendientes |
| 2026-10-02 | DOCUMENTAR 003-Modo visual por usuario | [Estado de esta fase](ESTADO_PROYECTO.md), [tareas](../specs/003-modo-visual-usuario/tasks.md) | Inspección y propuesta Markdown; pruebas funcionales, build, servidor y migración no ejecutados. Implementación pendiente de instrucción posterior |
| 2026-10-02, después de revisión/autorización | Implementar 003-Modo visual por usuario | [validation.md](../specs/003-modo-visual-usuario/validation.md) | 43 tests/check/migraciones/build OK, 59 HTML, cinco contratos JS, 180 contrastes, navegador cinco anchos/ambos modos y CSP sin scripts. 0002 solo en SQLite efímero. Zoom/preferencia reducida/autofill/revisión visual exhaustiva y aceptación pendientes |

| 2026-10-02 | DOCUMENTAR 004-UsuarioApp | [Validación documental](../specs/004-administracion-usuarios/validation.md), [estado](ESTADO_PROYECTO.md) | Solo Markdown; P-004-01/02 confirmadas. 12 documentos/105 enlaces válidos, 211 archivos no Markdown idénticos; siete RF/ocho tareas pendientes. Sin pruebas Django/build/servidor/migración; implementación no autorizada |
| 2026-10-02, después de revisión/autorización | Implementar 004-UsuarioApp | [Validación](../specs/004-administracion-usuarios/validation.md) | 57 métodos Django, check/esquema/build/60 HTML OK; navegador cinco anchos/ambos modos, acciones por rol, campos obligatorios/errores/foco/cancelar/sin scripts. MFA aislado por efecto lateral allauth. Envío válido por UI y aceptación pendientes; cero datos reales/migraciones nuevas o reales |

## Auditoría independiente y propuesta de actualización

| Fecha | Alcance | Evidencia | Resultado / límite |
|---|---|---|---|
| 2026-10-02 | Auditoría independiente de la base 001–004 | [VALIDACION_PREPRODUCCION.md](VALIDACION_PREPRODUCCION.md) | main/6bc1bd4, venv limpio con 47 pins actuales; 57 tests/check/esquema/60 HTML/build idéntico, deploy simulado, diagnóstico sintético y navegador. Con bloqueadores de dependencias/privilegios/integridad; sin correcciones, producción o aceptación |
| 2026-10-02 | DOCUMENTAR 005-Dependencias | [Validación documental](../specs/005-actualizacion-dependencias/validation.md) | Seis RF/siete tareas pendientes; candidatas resueltas con dry-run/no instaladas. P-005-01 migraciones allauth pendiente; no código actualizado |

## Regla vigente de actualización

- Registrar solo comandos y revisiones realmente ejecutados.
- Indicar el entorno, resultado y cualquier parte no comprobada.
- Mantener las pruebas por RF en [TRAZABILIDAD.md](TRAZABILIDAD.md) y el detalle reproducible en `validation.md` de la spec.
- No convertir el número de asociaciones RF/prueba en un porcentaje de cobertura ni en aceptación funcional.

## Correcciones posteriores autorizadas — 2026-10-02

005/006 ejecutadas con Python 3.12.14/Django 5.2.17 en .venv-actualizada, sin paquetes globales ni datos reales. **76 tests correctos**, pip check, check, esquema sin cambios propios, 61 HTML, build standalone idéntico. 52 paquetes Python + tres JS sin avisos devueltos por OSV; no certificación. Migración y restauración de fixtures antiguas, preflight colisiones/MFA, navegador de permisos/móvil/gráfico/CDN fallido. Guardado de credencial nueva por UI/aceptación y operación real pendientes. [Validación 005](../specs/005-actualizacion-dependencias/validation.md), [006](../specs/006-integridad-registro/validation.md), [guía](DEPENDENCIAS.md).
