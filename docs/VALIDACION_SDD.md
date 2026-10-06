# Validación de la entrega SDD reutilizable

Fecha: 2026-09-20. Alcance autorizado: agregar documentación SDD y manual a la base, sin modificar funciones ni crear módulos.

Este documento conserva la evidencia histórica de la entrega documental inicial. Después se aprobó e implementó [001-CalidadBase](../specs/001-calidad-seguridad-base/validation.md); sus resultados actuales sustituyen las observaciones de «cero tests» y ausencia de `core/test_settings.py` que describían el ZIP recibido.

## Fuente y comparación

Archivo recibido: core-base.zip.

SHA-256 de la entrada:

```text
c9612d8b1954455337338e5ff4026bf80ee980b1f9271d620f0c07786df94f34
```

Se compararon los 2.454 archivos originales extraídos contra el ZIP: **ningún archivo original modificado ni faltante**. Se agregaron 26 Markdown; no se crearon archivos ejecutables, migraciones ni una app de ejemplo.

## Controles realizados

| Control                                                        | Resultado                                                       |
| -------------------------------------------------------------- | --------------------------------------------------------------- |
| Comparación de bytes de archivos originales                    | Sin cambios                                                     |
| Enlaces relativos de nuevos Markdown                           | Válidos                                                         |
| Lectura sintáctica estática de Python propio                   | 29 archivos analizados sin errores sintácticos                  |
| Inspección de UsuarioApp/tests.py y homeApp/tests.py           | Cero métodos de prueba en ambos                                 |
| Comprobación de core/test_settings.py                          | No existe; se documentó la ausencia                             |
| Coherencia de nombres de plantillas, mixin y scripts npm       | Contrastados con los archivos reales                            |
| Reglas específicas de un negocio trasladadas a la constitución | Ninguna; requisitos de dominio corresponden a cada spec         |
| Specs de módulos de negocio creadas sin pedido                 | Ninguna                                                         |
| Flujo de autorización                                          | Primera fase documental; código solo tras instrucción posterior |
| Prompts                                                        | Coordinador y alternativa paso a paso documentados              |

La comprobación sintáctica lee y analiza archivos sin ejecutar Django, conectarse a datos ni crear cachés Python. No equivale a probar comportamiento.

## Límites

No se ejecutó una suite funcional: los archivos de tests recibidos son esqueletos y esta entrega no cambia código. Los resultados anteriores de [VERIFICACION.md](VERIFICACION.md) son históricos, no nuevas ejecuciones.

No se instalaron dependencias, levantó el servidor, ejecutaron migraciones, reconstruyó CSS ni probó el navegador. Tampoco se hizo una auditoría completa de seguridad.

Las observaciones existentes están en [OBSERVACIONES_BASE.md](OBSERVACIONES_BASE.md). No se corrigieron silenciosamente ni se transformaron en tareas autorizadas.

## Empaquetado

El ZIP final conserva los archivos de código/configuración versionable originales y añade documentación. Excluye .env y secretos locales, bases de datos, dependencias instaladas, cachés, entornos, staticfiles y archivos personales de media.

Se conserva solo media/profile.webp como imagen predeterminada de la base: se inspeccionó visualmente y corresponde a un avatar ilustrado genérico referenciado por el modelo. No se copian subidas de usuarios.

Estas exclusiones afectan únicamente al paquete de entrega; no borran los archivos del original.

## Uso

No se requieren migraciones ni recompilación por esta entrega. Leer [MANUAL_SDD.md](../MANUAL_SDD.md), proporcionar nombre y requerimiento, y usar [el coordinador](../prompts/00-orquestador.md). El siguiente módulo empezará con su propia especificación.
