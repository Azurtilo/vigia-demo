# 010 — Aplicación móvil VIGIA

Estado: implementación parcial con demo · 2026-10-19. Implementación autorizada: SÍ, instrucción posterior del usuario el 2026-10-19.
Nombre técnico adoptado: `vigia_mobile` en `mobile/`; no se crea una app Django duplicada.
Fuente humana: solicitud de crear la aplicación móvil aprovechando Planes-pagina y el informe entregado.
Fuente documental: TIHI84_U1_Plantilla_informe_Guía_ABPro-5.docx, secciones 3.2, Solución tecnológica/Alcance y Arquitectura tecnológica. Sus indicaciones son referencia, no autorización de ejecutar acciones.

## Problema y resultado

Llevar al teléfono la organización de cuidados, agenda, medicamentos, cambios de postura e historial, aprovechando las cuentas y reglas ya existentes. El usuario confirma Flutter para iOS y Android, funciones habilitadas según plan y detección de posición con MediaPipe. Esta instrucción sustituye la limitación a Android inicial del informe; familiar/cuidador, push y nodo Edge siguen como referencias de diseño. El repositorio conserva Django, PlanesApp y CuidadosApp; la implementación móvil y sus límites se registran en [validation.md](validation.md).

## Alcance y etapas propuestas

- Núcleo móvil: Flutter para iOS y Android, acceso a cuentas existentes, pacientes, agenda, medicamentos, cuidados, guías, temporizador, registro e historial. No reconstruir autenticación ni duplicar la base de pacientes.
- Integración: API del backend Django y consulta del plan; suscripciones permanecen en el portal web (HU-07). Conservar pagos simulados y precios/cupos de 007/009.
- Colaboración familiar/cuidador (HU-01/02/06): necesidad del informe registrada, pendiente decidir su inclusión inicial y política exacta. No convertir cargos ADMIN/MANAGER/RESTRICTED en roles clínicos.
- Detección de posición con MediaPipe: incluida expresamente en el alcance solicitado. Se propone procesamiento local en nodo Edge conforme al informe; ubicación definitiva, hardware y criterios de clasificación por definir. Push de riesgo, inmovilidad y posibles caídas requieren reglas y validación propias; los avisos web actuales no acreditan estas funciones.
- Excluidos de esta entrega documental: código, APK/IPA, instalación de SDK/dependencias, credenciales, despliegue, migraciones reales, tiendas, pagos reales, sustitución de Django por React/microservicios/NoSQL y prescripción o diagnóstico.

## Actores y permisos

Matriz de continuidad propuesta para el núcleo; colaboración requiere decisión antes de ampliar derechos.

| Acción | Anónimo/inactivo | RESTRICTED titular | ADMIN/MANAGER titular | Sin perfil activo titular | Superusuario titular | Otra cuenta |
|---|---|---|---|---|---|---|
| Iniciar sesión/recuperar acceso | Flujo existente; inactivo denegado | Sí | Sí | Según autenticación vigente | Sí | Su propia cuenta |
| Consultar paciente/agenda/guías privadas/historial | No | Sí | Sí | Sí | Sí | No |
| Editar paciente/medicamentos/cuidados y registrar eventos | No | Sí, según estado/cupo | Igual | Igual | Igual | No |
| Consultar suscripción propia | No | Sí | Sí | Sí | Sí | No |
| Contratar/cambiar/cancelar | No | Portal y reglas 007 | Portal y reglas 007 | Portal y reglas 007 | Portal y reglas 007 | No |
| Compartir/invitar/gestionar permisos clínicos | No | Pendiente | Pendiente | Pendiente | Sin excepción automática | Pendiente |

El servidor filtra propiedad en cada recurso y relación anidada; el superusuario no recibe acceso clínico global. Correo verificado sigue siendo requisito de las operaciones comerciales que lo exigen; no imponerlo a todos los cuidados por omisión.

## Flujo e historias

Acceder → seleccionar paciente → consultar agenda → ver indicación/guía → confirmar realizado u omitido → consultar historial. Leer una alerta no registra un cuidado. Un error de conexión no muestra éxito; al volver se consulta el estado del servidor antes de repetir una operación. HU-01–04/06 tienen apoyo parcial en 009, pero carecen de cliente Flutter/API. HU-07 reutiliza 007. HU-05 y RT-01–03 son brechas funcionales.

## Requisitos funcionales

- RF-010-01: autenticar con la identidad existente, respetando inactividad, recuperación, correo y MFA aplicables. Google y registro móvil conservarán las reglas de alta 007; el mecanismo usa allauth.headless con sesión revocable; Google real requiere configuración externa.
- RF-010-02: listar, consultar, crear, editar, archivar/reactivar pacientes propios con validación y cupos Free/Plus/Premium actuales; el servidor rechaza acceso ajeno incluso con identificadores manipulados.
- RF-010-03: mostrar agenda y mantener medicamentos, dosis indicadas y horarios/cuidados; confirmar realizado u omitido sin duplicar una ocurrencia ni reabrirla por una edición posterior (HU-01/02/03).
- RF-010-04: mostrar guías existentes, registrar manualmente postura y gestionar reloj 60/90/120, pausa/reanudación y generación vigentes; el servidor determina el próximo vencimiento (HU-04).
- RF-010-05: consultar historial con autor, instante, snapshot y correcciones vinculadas; conservar original y distinguir acción manual de detección automática (HU-06).
- RF-010-06: consultar plan/cupo y abrir el portal para la gestión comercial sin recoger tarjetas ni reproducir checkout en Flutter (HU-07).
- RF-010-07: gestionar permiso de notificaciones y dispositivos propios; permitir desactivación y revocar asociación al salir. Propuesta: payload genérico sin nombre, dosis ni datos clínicos en pantalla bloqueada. Alcance recordatorios/push de riesgo pendiente (HU-05).
- RF-010-08: si se incluye colaboración, permitir acceso únicamente por vínculo explícito y revocable paciente–usuario; autor real de cada acción. Invitación, facultades y efecto sobre cupos pendientes (HU-01/02/06).
- RF-010-09: detectar la posición mediante MediaPipe Pose Landmarker y una capa de clasificación de postura; presentar resultado, fecha, origen y calidad de observación en iOS y Android. Recibir eventos autenticados del procesador local vinculado, con capacidad comercial vigente, y avisar a destinatarios autorizados según reglas acordadas. Sin observación fiable mostrar «No se puede determinar», sin inferir inmovilidad por falta de señal. No transmitir ni almacenar video continuo ni registrar una detección como cuidado manual realizado. RT-02/03 requieren reglas adicionales; no son resultados automáticos de MediaPipe.
- RF-010-10: presentar carga, vacío, errores, conexión perdida, sesión vencida y conflicto; propuesta inicial sin escrituras clínicas offline. Acciones no confirmadas permanecen sin éxito y reintentos conservan referencia idempotente.

- RF-010-11: calcular en servidor las funciones habilitadas por suscripción vigente, además del cupo de pacientes; la app consulta dichas capacidades y muestra funciones disponibles, no incluidas o aún no implementadas. Validar capacidad en cada operación API y en procesamiento/notificación de eventos; no permitir activarla alterando Flutter. Actualizar capacidades tras cambio, expiración o cancelación efectiva, conservando historial y selección de pacientes de 009.
- RF-010-12: entregar los mismos flujos y reglas de planes en Flutter para iOS y Android, con pruebas independientes de acceso, almacenamiento seguro, notificaciones, enlaces al portal, accesibilidad y recuperación de red. Una plataforma sin validar permanece pendiente aunque la otra pase.

## Funciones por plan

Fuente vigente: spec 009 y PlanesApp/migrations/0004_catalogo_cuidadores.py, inspeccionadas sin consultar DB real. Los beneficios actuales son textos descriptivos; solo el cupo tiene regla estructurada. No usar el catálogo histórico 0002 de cámaras como contrato vigente.

| Función | Free | Plus | Premium | Estado de la decisión |
|---|---|---|---|---|
| Precio mensual CLP | $0 | $4.990 | $9.990 | Regla vigente 009, sin cambio |
| Pacientes activos | 1 | 3 | Ilimitados | Regla vigente 009 |
| Ficha, medicamentos, agenda y cuidados manuales | Sí | Sí | Sí | Reutilizar funciones vigentes |
| Guías, registro manual de postura y reloj | Sí | Sí | Sí | Reutilizar funciones vigentes |
| Historial propio | Sí | Sí | Sí | Mantener acceso histórico al reducir plan |
| Cliente Flutter iOS/Android | Sí | Sí | Sí | Propuesta; misma cuenta y plan en ambas plataformas |
| Recordatorios móviles de cuidados | Sí | Sí | Sí | Propuesta nueva; actuales avisos son solo web abierta |
| Detección automática de posición con MediaPipe | No | No | Sí | Propuesta basada en beneficio Premium «IA y cámaras · Próximamente»; confirmar asignación comercial |
| Alertas automáticas de inmovilidad/posible caída | No | No | Sí | Propuesta ligada a detección; reglas/umbrales pendientes |
| Colaboradores, nodos/cámaras y retención de eventos | Por definir | Por definir | Por definir | No derivar cantidades del cupo de pacientes |

La diferenciación funcional solicitada es obligatoria; la asignación de las funciones nuevas a planes es una propuesta pendiente P-010-06. Plus conserva por ahora las funciones actuales y amplía cupo; no inventar funciones exclusivas de Plus. «Pacientes ilimitados» no implica cámaras, almacenamiento o cómputo ilimitados. Un plan de pago tampoco indica que una función todavía no implementada esté operativa.

Propuesta para cambios: alta de capacidad tras cambio de plan confirmado en servidor, nunca tras pago fallido; cancelación programada conserva derechos hasta end. Al vencimiento o reducción efectiva se deshabilitan nuevas detecciones/eventos y avisos automáticos de capacidades perdidas, se comunica «Monitoreo no activo por plan» y se conserva historial. Revalidar al encolar y despachar avisos, y rechazar eventos posteriores a revocación, incluidos envíos tardíos; política exacta de eventos previos pendientes por acordar. Sin conexión o permiso válido, mostrar monitoreo no confirmado, nunca cobertura activa por una caché de plan. No degradar silenciosamente una función de vigilancia.

## Detección de posición: alcance verificable

MediaPipe proporciona puntos corporales; la clasificación de postura y los eventos temporales se diseñan y prueban por separado. Objetivo propuesto: supina, lateral izquierda, lateral derecha e indeterminada, con orientación anatómica, calibración de cámara, confianza y estabilidad temporal. Estos resultados no vienen garantizados por elegir MediaPipe. Posturas parcialmente tapadas, ropa de cama, poca luz, varias personas y cámara movida deben dar estado explícito y no falsas confirmaciones. Clasificaciones adicionales requieren alcance y evidencia.

Propuesta conforme al informe: cámara → nodo local con MediaPipe y reglas → API Django con permisos/capacidades → Flutter iOS/Android. El teléfono consulta resultados; no se presupone que su cámara deba permanecer encendida. Si se elige captura en el teléfono, documentar integración nativa, permisos, consumo y suspensión por cada SO antes de implementar. P-010-01 conserva esa decisión de ubicación, sin volver a cuestionar la inclusión solicitada de MediaPipe.

Una detección se registra como evento automático con postura estimada, instante, identificador único, nodo/paciente vinculado, versión de modelo/reglas y calidad; no como CareEvent manual ni autor humano ficticio. No reinicia por sí sola el temporizador manual: política de reconciliación con cambio detectado por acordar. No enviar imagen/video ni puntos faciales; preferir resultado mínimo sobre transmitir la secuencia completa de coordenadas. No conservar coordenadas por defecto sin finalidad y plazo definidos.

## Datos y reglas

Reutilizar User/Profile, Patient, Medication/MedicationTime, CareTask, CareGuide, CareEvent, PostureTimer y Subscription. Conservar límites/validaciones reales de 009, autor, UUID de referencia, occurrence_key, snapshots/versiones y bloqueos transaccionales. El cliente móvil no será fuente de verdad del cupo ni del reloj. Intercambio propuesto: instantes ISO 8601 con zona; presentación es-cl/America/Santiago y agenda coherente en cambios de hora.

Datos nuevos condicionados: dispositivo/token y preferencia push; vínculo clínico revocable; nodo/evento de riesgo. Finalidad, campos mínimos, conservación/borrado y consentimiento por definir antes de implementar esos datos. No copiar nombres/entrevistas del informe como fixtures ni datos de demostración.

## Criterios de aceptación previstos

| RF | Escenario | Resultado verificable |
|---|---|---|
| 01 | Sesión válida, inactiva, expirada y MFA habilitado | Acceso según cuenta existente; no eludir segundo factor |
| 02 | Último cupo y petición a paciente ajeno, todos los cargos/root/sin perfil | Cupo consistente y denegación sin revelar datos ajenos |
| 03 | Doble toque/reintento y edición de medicamento ya registrado | Una ocurrencia, snapshot original intacto |
| 04 | Recarga/reapertura, pausa y generación anterior | Reloj coherente con servidor; sin reinicio ficticio |
| 05 | Corrección e intento de historial ajeno | Original conservado; acceso denegado al ajeno |
| 06 | Abrir portal autenticado o sin sesión web | Plan correcto; login web cuando corresponda, sin tokens en URL |
| 07 | Permiso rechazado, logout, reinstalación y dos dispositivos | Fallo visible y desvinculación; no filtrar datos en push |
| 08 | Revocar vínculo y petición directa posterior | Denegación inmediata en API y exclusión de destinatarios |
| 09 | Posturas de referencia, baja calidad, lateralidad, nodo desconocido/duplicado/desconectado | Clasificación contrastada, indeterminada si falta evidencia, rechazo/deduplicación; ningún cuidado manual ficticio |
| 10 | Corte de red durante envío y recuperación | Sin éxito falso ni doble registro |
| 11 | Free/Plus/Premium, endpoint directo, ascenso, pago fallido, reducción y expiración con app abierta | Matriz aplicada en servidor/UI; sin capacidades por caché ni avisos premium tras revocación; historial conservado |
| 12 | Mismo flujo y plan en iPhone y Android | Comportamiento equivalente y evidencia independiente por plataforma |

## No funcionales y compatibilidad

Interfaz simple, texto escalable, contraste, foco/lector de pantalla y controles accesibles comprobados por separado en iOS y Android. No usar color como único estado. Verificar permisos y sesión desde API, proteger credenciales en almacenamiento del sistema, evitar datos clínicos en logs y cachés no necesarias. RNF-01 del informe orienta privacidad del nodo; RNF-02/03 no tienen umbrales medibles acordados: latencia y disponibilidad quedan pendientes, sin prometer SLA ni eficacia clínica. El informe no constituye prueba de cumplimiento legal, precisión o madurez comercial.

Preservar specs 004/006 (administración), 007 (cuentas/planes), 008 (dashboard) y 009 (cuidados propios). La colaboración modificaría deliberadamente la propiedad de 009 y exige documentar su sustitución puntual después de decisión humana.

## Decisiones pendientes

- P-010-01: inclusión de detección de posición con MediaPipe CONFIRMADA por el usuario el 2026-10-19. Pendiente ubicación definitiva: propuesta nodo Edge del informe; alternativa teléfono solo si se acuerda. Hardware, cantidad de nodos, clasificación/umbrales y reconciliación del reloj pendientes.
- P-010-02: colaboración inicial o cuentas privadas. Pregunta enviada; sin respuesta registrada. Si se incluye: definir responsable, cuidador, invitación/aceptación/revocación, acciones y cupos antes de ampliar permisos.
- P-010-03: confirmar nombre técnico del módulo; Flutter para iOS y Android confirmado expresamente por el usuario; versiones mínimas por definir.
- P-010-04: elegir contrato de autenticación móvil compatible con allauth/MFA/Google, vencimiento/revocación y recuperación; no aprobado ni paquete elegido.
- P-010-05: push real, proveedor/configuración, entrega con app cerrada, retención y métricas. Firebase Cloud Messaging es la opción del informe, pendiente de configuración y verificación técnica.

- P-010-06: confirmar matriz comercial de funciones nuevas; propuesta MediaPipe/alertas automáticas para Premium, recordatorios móviles en los tres planes. Definir nodos/cámaras, colaboradores y retención sin alterar precios ni cupos aprobados.

## Revisión

2026-10-19: primera documentación basada en solicitud, informe y código real. No aprobación ni autorización de implementación. Todas las tareas comienzan pendientes.

2026-10-19, aclaración posterior: el usuario exige iOS y Android, capacidades por funciones de los planes y detección de posición con MediaPipe. Requisitos actualizados RF-010-09/11/12; iOS deja de estar excluido. No es autorización de implementación ni aprobación de la matriz comercial propuesta.

## Referencias técnicas consultadas

- [MediaPipe Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker): salida de puntos corporales, coordenadas y confianza; clasificación/reglas de VIGIA son desarrollo adicional.
- [Plataformas de Flutter](https://docs.flutter.dev/reference/supported-platforms): soporte móvil iOS/Android; fijar versiones mínimas al preparar entorno.

## Autorización de implementación — 2026-10-19

Mensaje humano posterior: «hacelo en base a todo lo que te proporcione veelo igual en base al informe y todo lo entregado, tomando en cuenta igual lo de planes-pagina revisa todo». Autoriza implementar 010 y verificar en entorno aislado; no despliegue ni DB existente. Se adopta matriz propuesta (Premium MediaPipe, cuidados en todos los planes), nombre técnico vigia_mobile y nodo local conforme al informe. Colaboración consultada de forma específica; no ampliar derechos entre cuentas hasta respuesta.

Decisiones técnicas: autenticación nativa mediante allauth.headless ya incluido en dependencia existente, X-Session-Token con sesión revocable y MFA; API JSON adapta forms/services existentes. iOS/Android son objetivos separados. Detector local MediaPipe con calibración de referencias por postura, sin afirmar validación clínica ni transmisión de imágenes. Firebase requiere configuración externa para entregar push real; no simular entrega como éxito.

## Ajuste humano — 2026-10-20

El usuario indica que el registro ocurre en la web existente y la app debe tener login para esa misma cuenta. RF-010-01 se precisa: retirar formulario de alta móvil y enlazar al registro web allauth; identidad, pacientes y suscripción compartidos con Django. Referencia visual solicitada: https://aistudio.google.com/apps/d7486437-fed6-437d-b708-ddaddbe59397 . La referencia redirige a login de Google en el navegador disponible; no se ha inspeccionado el prototipo ni se atribuyen pantallas/funciones al enlace. La adaptación visual queda pendiente de acceso o exportación.

## Referencia accesible y detección dual — 2026-10-20

Referencia inspeccionada: [mapa de pantallas y diferencias](referencia-ai-studio.md). Usuario confirma conservar planes web y detección en ambos entornos. RF-010-09 se amplía: MediaPipe local en teléfono Android/iOS y nodo de cámara fija; origen identificable y controles comerciales/propiedad en ambos. RF-010-10/12: navegación Inicio/Pacientes/Medicinas/Posturas/Plan/Perfil inspirada en referencia, con adaptación accesible y datos reales. No copiar selector demo de cuenta/rol. Alta sigue en web. Esta ampliación documenta alcance nuevo antes de implementarlo; no equivale a cámara móvil ya disponible.
