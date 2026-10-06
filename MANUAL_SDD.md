# Manual SDD para tu base reutilizable

## 1. Cómo empezar: nombre del módulo y requerimiento

Primero escribe el nombre del módulo, por ejemplo **NuevaAPP**. Después explica con tus palabras qué debe hacer, quién lo usará y qué resultado esperas.

Para analizar requisitos amplios, usa preferentemente un **modelo de IA con razonamiento avanzado** entre los disponibles en tu herramienta. Aquí «avanzado» se refiere al modelo de IA, no al módulo Django. No es obligatorio un modelo concreto: el procedimiento y sus límites deben mantenerse con el que utilices. La elección del modelo la haces en la herramienta; escribir el prompt no lo cambia por sí solo.

Tu primer mensaje puede ser este:

```text
Nombre del módulo: NuevaAPP

Requerimiento:
[Aquí explico lo que necesito, usuarios, flujo, campos, permisos,
validaciones, ejemplos y lo que debe conservarse.
No hace falta que complete una entrevista ni sepa diseñar la base de datos.]

Fase: DOCUMENTAR, sin código.

Lee AGENTS.md y prompts/00-orquestador.md.
Analiza mi requerimiento, inspecciona esta base y selecciona los prompts
documentales que correspondan.
Genera primero spec.md, después plan.md y luego tasks.md, en la carpeta
numerada que corresponda dentro de specs.
Actualiza los documentos de docs y los índices que realmente lo necesiten.
No crees todavía la app, modelos, vistas, formularios, plantillas, JavaScript,
pruebas ejecutables ni migraciones.
Pregunta solo por decisiones críticas que no estén definidas.
Entrega los documentos para revisión y detente antes de implementar.
```

Reemplaza NuevaAPP por tu nombre real. No tienes que redactar RF ni elegir archivos: esa es parte del trabajo que hará la IA al analizar tu pedido.

**La primera entrega termina en documentos.** Que el plan describa modelos o rutas no significa que pueda crearlos todavía.

## 2. ¿Paso los prompts uno por uno?

**No es necesario. Para tu forma de trabajar, empieza con el prompt coordinador.**

| Modalidad | Qué haces tú | Qué hace la IA | Cuándo conviene |
|---|---|---|---|
| Coordinada | Das nombre, requerimiento y fase DOCUMENTAR | Lee las guías pertinentes y produce spec → plan → tasks, más docs afectados | Pedido claro; quieres avanzar sin copiar cada prompt |
| Paso a paso | Envías el prompt de especificación, luego plan y luego tareas | Entrega una fase por turno | Quieres revisar decisiones técnicas o un módulo complejo |
| Implementación por tareas | Tras revisar documentos, autorizas tareas concretas | Programa y prueba solo esas tareas | Cambios delicados o entregas pequeñas |
| Implementación del alcance completo | Tras revisar documentos, autorizas todas sus tareas | Avanza por tareas, prueba y actualiza evidencia | Alcance cerrado que ya revisaste |

La selección automática de prompts **no da permiso automático para programar**. El coordinador respeta la fase indicada. Tampoco hace falta pegar todo el contenido de prompts en el chat: puedes pedir que lea sus rutas si está trabajando dentro de esta carpeta.

Los prompts son guías, no ejecutables ni comandos especiales. No existe aquí un comando instalado como /spec. Si usas una herramienta que no puede leer archivos del proyecto, tendrás que compartir los documentos relevantes; no asumir que conoce el repositorio.

## 3. Qué debe producir la primera fase

Con un pedido concreto para NuevaAPP, el resultado esperado es una carpeta como `specs/001-nueva-app/`. Es una **ruta de ejemplo**; no existe ni está aprobada hasta que solicites ese módulo.

| Documento | Contenido esperado |
|---|---|
| spec.md | Problema, actores, alcance/exclusiones, requisitos identificados, datos, permisos, casos límite y criterios de aceptación |
| plan.md | Propuesta de integración en tu base, archivos, modelos/relaciones propuestos, validación, migraciones si aplican, pruebas y riesgos |
| tasks.md | Tareas pequeñas, orden, dependencias, RF y condición de terminado; casillas sin marcar |
| docs relacionados | Solo las actualizaciones necesarias de contexto, estado, decisiones, arquitectura propuesta e índice/trazabilidad |

La IA debe distinguir lo **existente**, lo **propuesto** y lo **pendiente de decisión**. No escribir que la app ya funciona, que se ejecutaron pruebas futuras o que aprobaste algo que todavía no revisas.

Cuando haya un vacío crítico, debe documentar lo que sí está claro. Ejemplo: si no definiste quién puede ver datos sensibles, no debe abrirlos públicamente por su cuenta. Puede dejar esa parte bloqueada con una pregunta concreta. No necesita detener todo para preguntarte nuevamente qué framework usa tu base.

## 4. Revisar y autorizar código

Lee primero la spec. Comprueba que entendió el negocio, roles y casos especiales. Después revisa el plan y las tareas al nivel que necesites.

Para corregir documentos sin programar:

```text
Revisa la spec 001: [explico la corrección].
Actualiza spec, plan, tareas y docs afectados.
Seguimos en fase DOCUMENTAR: todavía no implementes.
```

Cuando estés conforme, puedes enviar:

```text
Revisé spec.md, plan.md y tasks.md de specs/001-nueva-app.
Autorizo implementar el alcance descrito y sus tareas pendientes.
Usa prompts/04-implementar.md. Conserva mis cambios locales.
Si aparece una decisión crítica nueva o hace falta ampliar el alcance,
explícala antes de hacerlo. No despliegues ni toques datos reales.
Ejecuta las pruebas pertinentes y actualiza tareas, validación y estado.
```

Si prefieres avanzar poco a poco, cambia «sus tareas pendientes» por los IDs concretos, por ejemplo T-001-01 y T-001-02. Son IDs ilustrativos: utiliza los de tus documentos reales.

Esta separación en dos momentos es una preferencia explícita de esta base. Incluso si el pedido inicial dice «quiero crear una app», se empieza documentando y se espera una instrucción posterior de implementación. No hay que volver a pedir permiso para cada edición reversible que ya esté dentro de la implementación autorizada.

Autorizar código no autoriza implícitamente cuentas del hosting, envío de mensajes, datos productivos, commit/push o despliegue.

## 5. Qué archivos son generales y cuáles cambian por proyecto

| Archivo | Se reutiliza | Se personaliza |
|---|---|---|
| constitution.md | Principios de trabajo, integridad, claridad, privacidad y evidencia | Solo si acuerdas cambiar un principio |
| AGENTS.md | Forma de trabajar y convenciones técnicas reales de esta base | Si cambian estructura, comandos o políticas técnicas |
| MANUAL_SDD.md / prompts | El procedimiento | Ajustes de tu metodología |
| docs/ARQUITECTURA_BASE.md | Componentes de la base inicial | Evolución real; propuestas claramente separadas |
| docs/PROYECTO.md | Estructura para identidad y contexto | Nombre, objetivo, usuarios y alcance del producto |
| docs/ESTADO_PROYECTO.md | Formato del punto de continuación | Estado real en cada sesión |
| docs/DECISIONES.md | Decisiones metodológicas generales | Decisiones nuevas propias del producto |
| specs y trazabilidad | Plantillas y convenciones | Requisitos, tareas y evidencia de cada módulo |

Por ejemplo, «interfaz clara, adaptable a móvil» es un principio general. «Solo este cargo puede corregir este tipo de documento» es una regla del módulo y debe ir en su spec. No mezclar reglas específicas de un cliente con la base maestra.

La IA puede actualizar docs cuando el pedido lo requiera, pero no debe reescribir todos los archivos por costumbre. Una regla comercial nueva no justifica modificar la constitución.

## 6. Cómo reutilizar la base muchas veces

1. Conserva esta base maestra sin datos de clientes.
2. Crea una copia o repositorio independiente para el nuevo producto.
3. Abre esa carpeta de trabajo en tu herramienta de desarrollo.
4. Indica el nombre del producto si lo conoces, el nombre del módulo y sus requisitos.
5. Deja que la fase documental complete PROYECTO.md y la primera spec con información conocida; lo demás puede quedar pendiente.
6. Revisa los documentos y luego autoriza implementar.

No renombres core, las apps compartidas o las tablas solo porque el cliente cambie. El nombre del módulo nuevo no obliga a renombrar el proyecto Django existente.

Si partes de una copia que ya tiene otro negocio, no borres sus carpetas a ciegas. Es preferible usar esta base maestra limpia. Nunca reutilices el .env, base de datos o imágenes personales de un cliente en otro.

Una mejora general útil para todos los proyectos se lleva a la base maestra mediante una tarea propia y se distribuye revisando diferencias. No copies AGENTS o docs encima de un proyecto personalizado sin comparar lo que perderías.

## 7. Un ejemplo de pedido claro

**Ejemplo didáctico; no es una solicitud autorizada en esta entrega:**

```text
Nombre del módulo: SolicitudesAPP

Quiero que los usuarios autenticados creen solicitudes con título,
descripción y prioridad baja/media/alta.
RESTRICTED ve solo sus propias solicitudes.
MANAGER y ADMIN ven todas y pueden cambiar el estado:
pendiente, en proceso o cerrada.
El superusuario conserva el acceso completo de esta base.
No quiero borrar solicitudes ni adjuntar archivos en esta versión.
Necesito búsqueda, filtro por estado y listado paginado.
No quiero correos ni exportación todavía.

Primero genera spec, plan y tasks; sin código.
Usa el coordinador y actualiza los documentos necesarios.
```

Con un pedido así, la IA tiene bastante información para redactar sin entrevistarte. Si un caso no está definido —por ejemplo reabrir una solicitud cerrada— debe señalarlo como decisión pendiente cuando afecte el flujo, sin inventar una regla.

Un RF posible sería: «CUANDO un usuario con cargo RESTRICTED consulta una solicitud ajena, EL SISTEMA impide acceder a su contenido, también mediante URL directa». Su prueba deberá intentar ese acceso; no basta con ocultar el enlace.

## 8. Cambios, errores y nuevos módulos

| Petición | Flujo |
|---|---|
| Agregar campo o filtro pequeño | Actualizar spec vigente, plan/tareas afectados y registro fechado; después autorizar código |
| Añadir un módulo distinto | Nueva carpeta numerada; usar arquitectura y autenticación existentes |
| Corregir un error | Reproducir, comparar contra requisito, documentar arreglo y regresión; implementar cuando se autorice |
| Rediseñar una regla | Registrar qué decisión sustituye; ajustar specs dependientes |
| Consultar una idea | Solo análisis; no crear tareas aprobadas ni programar |
| Mejorar la base maestra | Spec propia con impactos en proyectos derivados y compatibilidad |

Una spec no tiene que equivaler siempre a una app. El plan explica si una vista pertenece a una app existente. La IA debe conservar tus nombres salvo una incompatibilidad real o una alternativa acordada.

## 9. Pruebas y finalización

Después de implementar, usar [05-validar](prompts/05-validar.md). La evidencia debe relacionar requisitos con resultados concretos.

Esta base todavía no trae pruebas funcionales en UsuarioApp/tests.py ni homeApp/tests.py, y no tiene core.test_settings. No copiar comandos ni conteos de pruebas de otros proyectos. El plan de cada módulo debe prever cómo probar de forma aislada.

Antes de aceptar, revisa:

- Resultado solicitado y exclusiones respetadas.
- Permisos comprobados en servidor, no solo en menú.
- Casos inválidos/límite relevantes.
- Interfaz utilizable y errores claros.
- Migraciones/efectos sobre datos explicados si existen.
- Pruebas realmente ejecutadas y límites registrados.
- Spec, tareas, validación y estado actualizados.

La verificación técnica y tu aceptación funcional son diferentes. No declarar «todo probado» si quedaron revisiones pendientes.

## 10. Pausar y continuar sin perder el avance

Antes de cambiar de sesión usa [07-retomar-pausar](prompts/07-retomar-pausar.md) en modo PAUSAR. Debe guardar en los Markdown lo hecho, lo pendiente, resultados reales y próxima acción.

Después pide:

```text
Modo RETOMAR. Lee AGENTS.md, docs/ESTADO_PROYECTO.md y la spec activa.
Comprueba archivos y cambios locales.
Continúa únicamente la fase y las tareas ya autorizadas.
Si la fase era documental, sigue sin crear código.
No vuelvas a empezar ni reconstruyas lo que ya está guardado.
```

No hace falta pegar el primer requerimiento entero otra vez. Sí debe existir un punto de reanudación real; una captura del chat no demuestra que los archivos se guardaron.

## 11. Regla corta para recordar

**Primero nombre y requerimiento. Luego documentos. Después revisión y autorización de código. Finalmente pruebas y estado actualizado.**

SDD organiza acuerdos y evidencia. No reemplaza las copias de seguridad, Git, tu revisión ni el criterio técnico. Se puede empezar solo con estos Markdown, sin instalar herramientas SDD adicionales.
