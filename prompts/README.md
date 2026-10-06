# Prompts: coordinados o por fase

**No tienes que enviarlos todos uno por uno.** Usa el coordinador con el nombre del módulo, requerimiento y fase DOCUMENTAR. La IA selecciona las guías documentales pertinentes y produce spec → plan → tasks. Se detiene antes del código.

Si prefieres revisar cada paso, usa 01, luego 02 y luego 03 en mensajes separados. Después de revisar los documentos, puedes autorizar 04 para tareas concretas o para el alcance completo. 05 sirve para validar; 06 para cambios y 07 para continuar.

| Archivo | Uso |
|---|---|
| [00-orquestador.md](00-orquestador.md) | Coordinar la fase adecuada |
| [01-especificar.md](01-especificar.md) | Especificar el resultado |
| [02-planificar.md](02-planificar.md) | Proponer integración técnica |
| [03-tareas.md](03-tareas.md) | Preparar pasos verificables |
| [04-implementar.md](04-implementar.md) | Implementar después de revisión |
| [05-validar.md](05-validar.md) | Validar con evidencia |
| [06-cambios.md](06-cambios.md) | Documentar un cambio o error |
| [07-retomar-pausar.md](07-retomar-pausar.md) | Pausar o retomar sin reconstruir |

El [manual](../MANUAL_SDD.md) incluye el primer mensaje completo y el mensaje posterior de autorización. Elegir automáticamente un prompt no concede permisos adicionales. Un prompt no cambia por sí solo el modelo de IA seleccionado ni instala herramientas.
