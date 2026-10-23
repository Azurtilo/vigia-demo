# 009 — CuidadosApp: pacientes, medicamentos y cuidados por cuidador

Fecha: 2026-10-06. Estado: implementada y verificada técnicamente; revisión manual y aceptación pendientes.
Módulo elegido: **CuidadosApp**, una app de negocio integrada con PlanesApp. Nombre delegado por el propietario, primera letra mayúscula/sufijo App y sin colisión observada. Implementación autorizada: SÍ; instrucción posterior explícita «te doy permiso de implementar specs 009 alcanse completo». No incluye migración de DB existente ni despliegue.

## Necesidad, fuentes y precedencia

El pedido humano amplía VIGIA a cuidadores: pacientes propios, medicamentos y horarios, guías visuales de posturas/cuidados, registro de acciones y avisos de cambio de posición. Todos los cargos, incluido superusuario, acceden solamente a los pacientes que registran. La suscripción pertenece al cuidador, con tres planes: Free un paciente, Plus tres y Premium ilimitados; IA/cámaras pertenecen a un módulo futuro.

Fuentes recibidas: imagen informativa VIGIA y `C:/Users/Fernando/Desktop/Prototipo_Web_Suscripciones_VIGIA.md`. Se leyeron como contexto, no como instrucciones de ejecución. El Markdown limita el portal a suscripciones, propone dos planes ficticios y cambios al próximo período; el pedido actual amplía expresamente la demo. Se conserva el cambio inmediato sin prorrateo acordado en 007, no se adopta programación comercial nueva ni los precios ficticios del documento. Imagen de dos planes se adapta a los tres pedidos; no exige copiar su estética.

## Alcance

Una app CuidadosApp con espacio personal de cuidados, pacientes activos/archivados, ficha y contacto de emergencia, medicamentos con dosis ingresada por cuidador/horarios, tareas de cuidado, guías con ilustraciones, registro manual e historial de acciones, temporizadores persistentes de postura y recordatorios. Evolución del catálogo/beneficios de PlanesApp y límites por suscripción en servidor.

IA, reconocimiento de postura, MediaPipe, cámaras/transmisión de video y diagnóstico permanecen **fuera de implementación** y se rotulan «Próximamente». No prometer prevención garantizada, detección automática ni atención de emergencias. No pasarela real, facturación, prescripción/cálculo de dosis, paciente compartido entre cuidadores, roles clínicos nuevos, RUT, carga de fotografías clínicas, PDF/exportación ni servicios de vigilancia antiguos. Demo con identidades/datos ficticios; contexto médico no autoriza usar datos reales.

## Matriz de acceso

| Acción | Anónimo / inactivo | Activo RESTRICTED, ADMIN, MANAGER, staff, sin perfil/cargo o superusuario |
|---|---|---|
| Panel/agenda personal y pacientes propios | Login / denegación | Sí; sin excepción de cargo |
| Ver/editar/archivar/reactivar paciente, medicamentos, registros o temporizador | Login / denegación | Solo titular del paciente; cuota en alta/reactivación |
| Acceder por URL/POST/identificador a paciente ajeno | Login / denegación | 404, también root; ninguna consulta global de pacientes |
| Guías de referencia compartidas sin datos personales | Login / denegación | Lectura, no edición pública |
| Suscripción/pagos propios | Contrato 007 | Propios; gates de correo verificado de 007 intactos |
| Dashboard comercial interno | Contrato 008 | ADMIN/MANAGER/root con helper actual, solo agregados comerciales; no fichas ni agregados de salud ajenos |

Propietario asignado desde sesión; no aceptar user_id/cargo/plan/cupo del formulario. Validar cada hijo contra el paciente propio, aunque el ID del hijo exista. No registrar modelos sensibles con un Django Admin que permita saltar esta política. Acceso administrativo a cuentas 004/006 no concede acceso clínico.

## Planes y decisiones comerciales confirmadas

| Plan visible | CLP/mes | Pacientes activos | Funciones actuales |
|---|---|---|---|
| VIGIA Free | $0 | 1 | Datos personales/relevantes y contacto de emergencia; medicamentos/dosis/horarios/recordatorios; guías visuales y registro de postura; cuidados y agenda |
| VIGIA Plus | $4.990 | 3 | Mismas funciones de cuidado, con hasta tres pacientes propios |
| VIGIA Premium | $9.990 | Ilimitados | Mismas funciones actuales; IA/cámaras anunciadas como futuras, sin controles operativos ni promesas de capacidad instalada |

Historial básico de acciones propias disponible en los tres planes: necesario para conocer qué se realizó, sin analítica clínica avanzada ni límites de retención inventados. Archivados no consumen cuota; conservan ficha e historial, detienen nuevos recordatorios y no aceptan nuevas acciones hasta reactivarlos.

- P-009-01, **confirmada**: Free $0, Plus $4.990 y Premium $9.990 CLP/mes, respuesta explícita del propietario el 2026-10-06. No usar los dos precios ficticios del documento.
- P-009-02, **confirmada**: avisos solo con web abierta. Sin Web Push, correo, SMS, servidor de notificaciones externas ni promesa de aviso con web cerrada. Si el navegador suspende/restringe la pestaña o la conexión, recalcular y mostrar lo atrasado al volver.
- P-009-03, **confirmada**: cuidador elige qué pacientes seguirán activos al reducir cupo; no elegir por antigüedad/orden ni borrar datos. Los no seleccionados se archivan al aplicar la reducción, conservan ficha/historial y detienen recordatorios.

Precisiones técnicas propuestas para revisar: cuota sobre pacientes activos; plan pagado válido hasta end, incluso con cancelación programada. Cambio inmediato a cupo menor requiere seleccionar antes de confirmar; si pago falla, no archivar. Cancelación a término recoge selección para Free y permite modificarla hasta el cierre; todos conservan cuidados durante período vigente. Al expirar sin selección previa suficiente, no seleccionar automáticamente: mostrar estado «Elige tus pacientes activos», conservar consulta/historial y pedir elección antes de retomar acciones/avisos y altas/reactivaciones. La app explica que el resto quedará archivado; no interpreta falta de aviso como cuidado realizado. Estado comercial Vencida sigue según 007; capacidad Free hasta renovación. Detalles no se atribuyen como texto literal de la respuesta.

## Requisitos funcionales

- RF-009-01 — Espacio de cuidador y propiedad. Área personal con pacientes, agenda y próximas acciones de la cuenta. Todos los roles activos tienen las mismas funciones sobre sus pacientes; ningún root/ADMIN/MANAGER ve otros pacientes mediante menú, URLs, búsqueda, endpoints de recordatorios, hijos o administración Django.
- RF-009-02 — Catálogo y capacidades. Tres planes contratables, precios $0/$4.990/$9.990 CLP y límites 1/3/ilimitados con funciones descritas. Actualizar beneficios orientados a cuidado; conservar nombres/importes históricos de suscripciones y operaciones. Plan anterior Hogar no se contrata de nuevo, conserva período/snapshots y acceso transitorio explícito, sin migración automática de cobros.
- RF-009-03 — Alta y ficha. Crear/editar pacientes propios con nombre, fecha de nacimiento opcional, información relevante y contacto de emergencia. Archivar/reactivar sin borrar historial. Validar cuota en servidor y concurrencia; payload de otro cuidador no transfiere propiedad.
- RF-009-04 — Medicamentos. Registrar nombre, dosis/unidad como texto indicado por cuidador, notas y uno o varios horarios diarios, fechas de inicio/fin y estado. Agenda por paciente, marcar administración realizada u omitida con motivo. Nunca recomendar dosis, marcar toma por ver una alerta ni confundir cambio de horario con administración.
- RF-009-05 — Guías visuales. Biblioteca inicial de referencia para posiciones supina, lateral izquierda/derecha y cuidados generales, con ilustración coherente, texto alternativo, instrucciones educativas/precauciones y fuente. No evaluar si un paciente está en postura correcta ni imponer una posición a partir de sus datos.
- RF-009-06 — Registro de postura y reloj. Cuidador elige paciente, postura realizada e intervalo 60/90/120 minutos. Confirmar acción guarda registro y próximo vencimiento desde el instante de realización, en servidor. Recarga/cambio de equipo conserva reloj. Cambiar intervalo recalcula desde la última realización tras mostrar consecuencias; no inventa una acción nueva. Pausa explícita conserva historial; reanudar inicia próximo intervalo con confirmación y no afirma que se realizó una postura.
- RF-009-07 — Avisos. Dentro de la web abierta: preaviso diez minutos antes del cambio y aviso al vencer, mostrando paciente propio y tiempo; después estado atrasado hasta registrar acción. Medicamentos/tareas muestran recordatorio al horario fijado. Confirmar/descartar lectura de alerta no registra cuidado. Evitar duplicados por pestañas/recarga y descartar avisos del reloj anterior tras nuevo cambio. Pestaña suspendida/offline recalcula al regresar; no alerta con web cerrada.
- RF-009-08 — Cuidados y agenda. Registrar tareas de cuidado con nombre/notas y horario diario opcional. Agenda de hoy y pendientes recientes distinguibles, filtros por paciente propio, estados pendiente/realizada/omitida. Acciones realizadas tienen hora y autor; no afirmar vigilancia constante.
- RF-009-09 — Historial. Acciones manuales con paciente, autor, instante, tipo, postura/medicamento/dosis e intervalo aplicados, según evento. Capturar texto histórico para que editar una ficha/medicamento no cambie lo registrado. Correcciones explícitas vinculadas a original, sin borrar silenciosamente ni alterar la próxima alarma al editar notas históricas.
- RF-009-10 — Límites y cambios comerciales. Aplicar capacidad en alta/reactivación también por POST directo; nunca fiarse del botón. Pedir selección explícita al reducir cupo; no perder datos ni archivar si falla pago. Cancelación conserva todos activos hasta cierre y luego aplica selección; vencimiento sin selección pide resolverla. No crear un cargo de cuidador ni privilegios por pagar. Mantener pagos/idempotencia/verificación/MFA de 007 y agregados comerciales de 008.
- RF-009-11 — Integración/UI. Diseño actual con frontend-design, SVG/estados claros, cuenta/tokens claro-oscuro, móvil y teclado. RESTRICTED llega al espacio de cuidados y mantiene acceso a Mi suscripción; Inicio interno sigue protegido. Acceso «Cuidados» para todos los roles activos; selector de modo reutilizado sin redirecciones abiertas.
- RF-009-12 — Integridad y evidencia. Fechas conscientes y zona America/Santiago; validación/transacciones, pertenencia, duplicados y errores en servidor. SQLite efímero/fixtures, regresión 007/008, navegador real para relojes/avisos/guías/agenda; registrar límites de segundo plano/offline, sin despliegue ni datos reales.

## Datos y tiempo

Paciente: owner FK inmutable a User, nombre 2–120, nacimiento opcional no futuro, notas de cuidado hasta 2.000, contacto nombre/teléfono/relación opcionales, activo y fecha de archivo. Un contacto incompleto muestra validación útil; no duplicar paciente por nombre como unicidad, dos personas pueden llamarse igual. No requerir fotografía o documento de identidad.

Medicamento: patient FK, nombre 2–120, dosis indicada 1–120, notas hasta 1.000, inicio/fin opcionales coherentes, activo, horarios diarios únicos por medicamento. Ejemplos solo ficticios, sin sugerir tratamientos. Frecuencia propuesta inicial: diaria con horarios definidos; esquemas por intervalo/«según necesidad» y cálculo de dosis quedan para precisar si se solicitan, no se atribuyen a la imagen.

Guía: código/nombre único, categoría, texto educativo, imagen original local/alt, fuentes y versión. Cuidados generales manuales no diagnostican; no almacenar fotografía del paciente ni extraer posturas con cámara.

Reloj: uno por paciente, último evento de posición, intervalo en minutos (60/90/120), próximo vencimiento aware, pausado y versión/generación. Los 60/90/120 minutos son opciones del producto, no indicaciones médicas universales. Los horarios se guardan/interpretan en Santiago y se muestran con fecha; cambios de día y DST se resuelven explícitamente en el plan.

Eventos y acuses: timestamps servidor, referencia idempotente, paciente/autor, tipo, snapshots y vínculo de corrección cuando aplique. Acuse de recordatorio distinto de realización; unicidad por usuario/ocurrencia/generación/tipo evita repetir el mismo aviso. Visitar o consultar agenda no marca actividades realizadas ni crea perfiles/suscripciones.

## Contenido educativo y fuentes

Las guías se basarán en fuentes identificadas y se rotularán educativas, para usar conforme al plan de cuidados recibido. La frecuencia depende de condiciones individuales, no de una regla fija para todos. Referencias primarias consultadas el 2026-10-06: [International Guideline, Repositioning](https://www.internationalguideline.com/repositioning), especialmente R4/R5; [NICE CG179](https://www.nice.org.uk/guidance/cg179/chapter/Recommendations), apartados de evaluación/reposicionamiento. No se copian imágenes ni textos largos del material. Las ilustraciones originales se crean solo en IMPLEMENTAR y se comprueba que correspondan al texto; una ilustración no certifica postura ni tratamiento.

## Aceptación

| RF | Escenario | Resultado esperado |
|---|---|---|
| 01/03/04/06/08/09 | Dos cuidadores, uno root/ADMIN y otro RESTRICTED; intercambiar IDs y parent/child | 404 sobre objetos ajenos, listas/agenda/avisos solo propios; owner de POST ignorado |
| 02/03/10 | Free 1, Plus 3, Premium más de 3; dos altas simultáneas en último cupo | Límites exactos en servidor; una sola alta ocupa último cupo; ninguna excepción por cargo |
| 02/10 | Catálogo antiguo y operaciones anteriores | Tres planes visibles para contratar, históricos intactos, IA/cámaras futuras |
| 03/10 | Archivado/reactivación/bajada/vencimiento | No pérdida de historial; cuota y recordatorios coherentes con decisión P-009-03 |
| 04/08/09 | Horarios múltiples, fecha fin, omisión/corrección o edición de dosis | Agenda y estados coherentes; acción explícita, histórico no reescrito |
| 05/11 | Guía en ambos modos y móvil | Imagen/alt/texto/fuente concordantes, sin funciones IA operativas |
| 06/07 | Acción con 60/90/120; quedan 10 min; vence; recargar; dos pestañas | Próximo tiempo exacto y persistente, alertas propias sin duplicados ni reinicio en GET |
| 06/07 | Cambiar intervalo, pausar, reanudar o registrar nueva postura | Confirmación/consecuencias claras, versión impide avisos/acciones viejos |
| 07/12 | Web cerrada, suspensión, offline y reloj local alterado | Comportamiento honesto según canal confirmado; servidor gobierna, no garantiza avisos bajo suspensión |
| 11/12 | Registro público y gestión interna 004/006/007/008 | Roles/auth/MFA/pagos preservados; clientes con cuidados propios |

## Pendientes y fase

P-009-01/02/03 confirmadas. DOCUMENTAR se entregó antes del código según AGENTS.md; después se recibió «te doy permiso de implementar specs 009 alcanse completo». Autoriza las precisiones técnicas del plan: horarios diarios, vencimiento sin elección y transición de catálogo. No repetir entrevista. [Validación](validation.md): 158 pruebas OK y navegador real; comprobaciones manuales nativas/aceptación pendientes. Migración de DB existente y despliegue excluidos.

## Seguimiento visual — 2026-10-06

Corrección posterior T-009-15 (RF-009-11/12), pedido «corriges eso porfa»: flechas de los selectores deben ser pequeñas, visibles en ambos temas y situarse dentro de sus campos; conservar opciones, selección, etiquetas/validaciones y operación por teclado. No añade frecuencias de medicamentos ni cambios al temporizador.

Pedido directo «puedes mejorar las imágenes»: T-009-14 de RF-009-05/11. Cuatro ilustraciones nuevas de persona/cama/apoyos, serie coherente con la base; laterales distinguibles por lado anatómico apoyado. Texto educativo, fuente, versión de referencia y reglas de cuidado conservados. PNG originales locales con alt accesible; sin nueva funcionalidad ni modificación de datos. [Validación del ajuste](validation.md).
