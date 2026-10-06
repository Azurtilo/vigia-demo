# Coordinar la fase adecuada

Puedes pedir a la IA que lea este archivo en el proyecto. Si copias el mensaje, reemplaza los campos entre <...>. Los nombres/IDs de ejemplo no son trabajo autorizado.

```text
Lee AGENTS.md, constitution.md, docs/PROYECTO.md, docs/ESTADO_PROYECTO.md y specs/README.md. Inspecciona el estado real de los archivos y la spec afectada antes de proponer cambios.

Entrada del usuario:
- Nombre del módulo: <NombreAPP>.
- Requerimiento: <texto libre>.
- Fase: DOCUMENTAR, salvo una autorización posterior explícita de otra fase.

Selecciona las guías de prompts que correspondan y explica brevemente cuáles usarás:
- Para módulo nuevo: 01-especificar, 02-planificar y 03-tareas, en ese orden.
- Para cambio o bug: 06-cambios y después las fases documentales necesarias.
- Para continuar: 07-retomar-pausar respetando el estado y autorización existentes.
- Usa 04-implementar o 05-validar solo si la fase correspondiente fue solicitada. Encontrar un prompt en esta carpeta no autoriza ejecutarlo.

En DOCUMENTAR crea primero spec.md, después plan.md y finalmente tasks.md, en la carpeta del siguiente número libre; para cambios pequeños actualiza la spec vigente.
Actualiza únicamente docs/PROYECTO.md, docs/ESTADO_PROYECTO.md, docs/DECISIONES.md, docs/TRAZABILIDAD.md, arquitectura e índices que lo necesiten. Marca arquitectura nueva como propuesta, no implementada.
No modifiques constitución ni reglas generales para acomodar un requisito comercial.
No crees código, apps Django, pruebas ejecutables, migraciones, dependencias o prototipos.
No entrevistes por rutina: reutiliza información clara y pregunta solo por decisiones críticas ausentes. Deja partes bloqueadas explícitas sin inventar respuestas.
Entrega enlaces/rutas de documentos, decisiones pendientes y resumen. Detente antes de implementar y espera mi revisión e instrucción posterior.
```
