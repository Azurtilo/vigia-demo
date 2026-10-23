# Plan técnico — 010 / Aplicación móvil

Spec: [spec.md](spec.md). Estado: implementación autorizada el 2026-10-19; propuesta previa conservada como antecedente.

## Inspección de la base

Git presenta numerosos cambios locales y CuidadosApp/009 sin seguimiento; preservarlos. Existen core/urls.py (/accounts/, /planes/, /cuidados/), core/common_settings.py (LOCAL_APPS), PlanesApp/permissions.py (ClientMixin), CuidadosApp/permissions.py, models.py, services.py, scheduling.py y capacity.py. own_patient filtra owner incluso para root. CareEvent tiene referencias y restricciones de duplicidad; servicios usan tokens de acción firmados ligados a usuario/recurso/versión. No asumir que ese contrato HTML es una API móvil disponible.

## Diseño original y ejecución

Cliente Flutter para iOS y Android separado en mobile/ (creada tras autorización). Ampliar apps Django existentes con adaptadores API; no crear automáticamente MovilApp ni duplicar servicios/datos. Registrar include versionado propuesto /api/v1/ en core/urls.py después de autorización. Mantener portal Django/Templates y base relacional: React, NoSQL y microservicios del informe difieren de la base y no se adoptan silenciosamente. Esta desviación debe revisarse si se exige fidelidad literal a la arquitectura académica.

## Mapa por requisito

| RF-010 | Existentes | Archivos propuestos | Evidencia futura |
|---|---|---|---|
| 01 | UsuarioApp/adapters.py, allauth, core/common_settings.py | UsuarioApp/api/, mobile/lib/auth/ | Login/inactivo/MFA/Google/revocación |
| 02–05 | CuidadosApp/models.py, services.py, capacity.py, scheduling.py | CuidadosApp/api/, mobile/lib/care/ | Propiedad, cupos, doble registro, reloj e historial |
| 06 | PlanesApp/models.py, services.py, urls.py | PlanesApp/api/, mobile/lib/subscription/ | Plan propio/enlace seguro al portal |
| 07 | ReminderReceipt; avisos web existentes | CuidadosApp/notifications/, mobile/lib/notifications/ | Permiso, logout, entrega iOS/Android real |
| 08 | Patient.owner y own_patient | Política compartida y migración solo si acordada | Matriz por acción y revocación |
| 09 | Sin detector operativo; guías y eventos manuales 009 | Procesador MediaPipe local, clasificador y adaptador Edge propuestos | Posturas/lateralidad, observación inválida, emisor ajeno, duplicidad y desconexión |
| 10 | Versiones, referencias y transacciones actuales | mobile/lib/core/, pruebas API/móvil | Corte de red, recuperación, conflicto |
| 11 | Plan/Subscription y catálogo 0004, capacity.py | PlanesApp/entitlements.py y API de capacidades propuestos | Free/Plus/Premium, cambios/expiración, petición directa y tareas en cola |
| 12 | Sin cliente móvil existente | mobile/ios/, mobile/android/ e integración por plataforma propuestos | Paridad de flujos y evidencia separada iOS/Android |

Todos los directorios nuevos son previstos. Las rutas internas finales dependen del contrato de autenticación y decisiones de alcance.

## Capacidades por plan

Añadir servicio propuesto PlanesApp/entitlements.py que derive el plan efectivo con las reglas de Subscription/PlanesApp.services y devuelva capacidades estables, límites, vencimiento y versión. No inferir permisos del nombre visible, precio ni textos PlanBenefit. El código comercial existente `pro` corresponde a Premium; no renombrarlo ni usar el antiguo plan Hogar como plan nuevo. Revisar continuidad histórica de Hogar antes de resolver sus capacidades, sin habilitarle MediaPipe por omisión.

Claves propuestas: care_manual, medication_schedule, posture_manual, care_history, mobile_reminders, posture_detection, risk_alerts; límites separados max_active_patients y, al acordarlo, max_nodes. La matriz de spec es propuesta pendiente P-010-06. Definir configuración estructurada versionada o modelo de capacidades tras cerrar matriz; no añadir un booleano disperso por pantalla ni ejecutar migraciones ahora.

API de capacidades propias propuesta dentro de /api/v1/, consumida al iniciar sesión, recuperar conexión y regresar del portal. Cada operación vuelve a comprobar derechos, propiedad y estado del paciente en servidor; repetir verificación antes de aceptar evento del nodo y enviar push. Diferenciar función no incluida, función no implementada y dispositivo desconectado. En reducción/fin de período, usar selección/archivo 009 y preservar historial. Probar eventos en tránsito, sesión en dos teléfonos y carrera cambio de plan/operación. Plazo de autorización local del nodo y comportamiento sin red deben definirse antes de afirmar revocación de captura; el backend rechaza nuevas operaciones sin derechos vigentes.

## MediaPipe y motor de postura

Propuesta: nodo local conforme al informe, con Pose Landmarker y clasificador de VIGIA. MediaPipe obtiene landmarks; VIGIA debe clasificar postura y evaluar estabilidad temporal. Diseñar calibración, postura indeterminada, oclusión, orientación de cámara y varias personas; no convertir la ausencia de detección en inmovilidad. Inmovilidad y posible caída requieren reglas distintas y un conjunto de evaluación etiquetado con métricas/umbrales acordados, no deducidos de demos.

Contrato propuesto: event_id, node_id, patient_id vinculado en servidor, observed_at, posture, calidad, model_version y rule_version. Autenticación/revocación del nodo independientes del login humano; idempotencia por nodo/evento, validación de reloj atrasado y límites de frecuencia. Resultado automático en registro separado del CareEvent manual, relacionado al paciente y visible en historial sin falsificar autor. Transmitir metadatos mínimos, sin video ni puntos faciales; retención pendiente.

Flutter en iOS/Android consulta la misma API y presenta postura estimada, última observación y estado del monitoreo. Cámara del teléfono sería alternativa a acordar, con integración específica por SO; no elegir plugin Flutter MediaPipe por nombre sin verificar soporte. Los intervalos manuales 60/90/120 se preservan hasta acordar si un cambio automático puede reiniciar algún reloj. Nodo/modelo/versión/hardware y criterios de aceptación se fijan antes de implementar detector, sin prototipo encubierto en DOCUMENTAR.

## Datos y contratos propuestos

Lectura: identidad propia, pacientes, agenda por fecha, guías, reloj, historial paginado y suscripción propia. Escritura: cambios de paciente, medicamento/cuidado, registro de ocurrencia, postura/reloj y corrección. No crear endpoints ejecutables en esta fase.

Antes del código, detallar en Markdown método/ruta/campos, tamaños, paginación, filtros, errores de validación, 401/403/404/409, referencia idempotente y versionado. Evitar enumeración de objetos ajenos; nunca confiar en owner/autor enviados por Flutter. Reutilizar orden de bloqueo User/Subscription y servicios 009; adaptar contratos firmados sin eliminar control de estado/versiones. Probar repetición simultánea desde web y móvil. Errores no exponen trazas ni datos privados.

Autenticación requiere decisión técnica independiente: verificar capacidades/versiones instaladas de allauth para cliente nativo, Google y MFA; proponer mecanismo de sesión/token y revocación antes de elegir paquetes. No reutilizar contraseña en webviews ni añadir claves de servidor a la app. Portal abre URL fija conocida; no transportar credenciales por query string.

## Permisos e interfaz

Aplicar matriz de spec a consulta, detalle, anidados y mutaciones. Un cargo interno no equivale a permiso clínico. Si se aprueba colaboración, centralizar autorización por vínculo para web/API/servicios y destinatarios push; definir compatibilidad de registros existentes por owner y política al revocar. No basta modificar el listado Flutter.

Pantallas previstas: acceso, pacientes, resumen de paciente, agenda, medicamentos/cuidados, guías/postura, historial y consulta de plan. Push y gestión de colaboradores dependen de alcance. Mantener lenguaje y colores de la base como referencia; Flutter necesita widgets propios y validación visual iOS y Android. El portal conserva components/Layout/base_pages.html y navegación existentes.

## Migraciones y reversión

API/núcleo puede reutilizar tablas actuales. Sesiones móviles, dispositivos push, colaboración y eventos Edge podrían exigir tablas aditivas: definirlas tras decisiones, sin reescribir migraciones históricas ni asignar acceso masivo. Ensayar migración/reversión en datos ficticios, preservar historial y deshabilitar rutas nuevas como reversión de aplicación. Aplicación sobre DB existente, respaldo operativo y despliegue requieren autorización aplicable separada.

## Plan de pruebas

Tras autorización, leer docs/ENTORNO_Y_VERIFICACION.md y usar core.test_settings. Ejecutar regresión UsuarioApp/homeApp/PlanesApp/CuidadosApp y nuevas pruebas API de pertenencia, actor inactivo, sin perfil, RESTRICTED, ADMIN, MANAGER y root. Cubrir cupo concurrente, ocurrencias, correcciones, DST/medianoche, versiones caducadas y rollback.

Flutter: análisis, pruebas de comportamiento y widgets útiles; integración contra backend aislado con datos ficticios. Simulador/emulador y dispositivos iOS/Android para acceso, navegación, texto escalado, lector de pantalla, doble toque, suspensión, recuperación de red, logout y ausencia de datos de otra cuenta. Push: dispositivo real/app primer plano/segundo plano/cerrada, rechazo de permiso y desvinculación. MediaPipe: evaluación local con muestras autorizadas o sintéticas identificadas, lateralidad/supina y casos indeterminados; luego integración con hardware y condiciones representativas. Registrar precisión por clase, falsos eventos y latencia medida con umbrales pendientes de acuerdo. Una simulación no acredita detección real. Pruebas por cada plan en ambos SO, cambio de plan durante uso y detección/push bloqueados por API pese a manipular el cliente. No declarar iOS validado por pruebas Android. Preparar firma y distribución de pruebas iOS según entorno disponible, sin publicar ni solicitar certificados privados dentro del repositorio. Las 158 pruebas históricas no validan el móvil.

No ejecutar check/tests/build ahora: solo cambian Markdown. Tailwind solo corresponde si una futura implementación modifica estilos/clases/fuentes web.

## Riesgos, dependencias y decisiones

SDK Flutter, Android y herramientas iOS/Xcode, máquina de pruebas y versiones por verificar antes de instalar; no declarar herramientas disponibles por inferencia. Paquetes API/autenticación/push sin seleccionar; comprobar documentación oficial y compatibilidad durante definición técnica. Sin credenciales ni configuraciones cloud solicitadas en DOCUMENTAR. Push no equivale a entrega garantizada; definir observabilidad/estado y umbral medible antes de aceptación. No adoptar afirmaciones clínicas/legales del informe como comprobadas.

MediaPipe e iOS/Android están incluidos por instrucción humana. P-010-01 conserva ubicación/hardware/reglas pendientes y P-010-02 colaboración; P-010-03/04/05/06 deben quedar resueltas para sus tareas dependientes. Aunque se resuelvan, implementar requiere instrucción posterior explícita. Actualizar índice, proyecto, estado, decisiones y trazabilidad como propuestas.

## Revisión documental — 2026-10-19

Aclaración humana incorporada: Flutter iOS/Android, funciones por plan y MediaPipe incluidos. Tareas 13–15 amplían contrato de capacidades, detector y validación. No código autorizado. Referencias técnicas: [MediaPipe](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker) y [Flutter](https://docs.flutter.dev/reference/supported-platforms).

## Autorización de implementación — 2026-10-19

Mensaje humano posterior: «hacelo en base a todo lo que te proporcione veelo igual en base al informe y todo lo entregado, tomando en cuenta igual lo de planes-pagina revisa todo». Autoriza implementar 010 y verificar en entorno aislado; no despliegue ni DB existente. Se adopta matriz propuesta (Premium MediaPipe, cuidados en todos los planes), nombre técnico vigia_mobile y nodo local conforme al informe. Colaboración consultada de forma específica; no ampliar derechos entre cuentas hasta respuesta.

Decisiones técnicas: autenticación nativa mediante allauth.headless ya incluido en dependencia existente, X-Session-Token con sesión revocable y MFA; API JSON adapta forms/services existentes. iOS/Android son objetivos separados. Detector local MediaPipe con calibración de referencias por postura, sin afirmar validación clínica ni transmisión de imágenes. Firebase requiere configuración externa para entregar push real; no simular entrega como éxito.

## Archivos reales de esta implementación

- `mobile/lib/main.dart`, `api.dart`, `care.dart`, plataformas iOS/Android y assets de guías. Se mantiene agrupación simple; no se crean las subcarpetas inicialmente propuestas por rutina.
- `CuidadosApp/api/{base,views,detection,devices,urls}.py`; `PlanesApp/entitlements.py`; allauth.headless en configuración/rutas existentes.
- `CuidadosApp/mobile_models.py` y migración aditiva `0004_detectionnode_mobiledevice_postureobservation_and_more.py`. Importación de modelos desde models.py. Solo migrada en demo/pruebas.
- `edge/{run,posture,smoke,test_posture}.py`, requisitos separados y README; dependencia opcional `requirements-push.txt` y comando `send_mobile_reminders`.
- `core/mobile_demo_settings.py`, `core/mobile_demo_urls.py`, comando `seed_mobile_demo`; DB ficticia aislada.
- Pruebas `CuidadosApp/test_mobile.py`, `mobile/test/widget_test.dart`; [validación](validation.md) y [guía](../../docs/MOVIL_DESARROLLO.md).

No Tailwind nuevo en 010: interfaz Flutter, sin cambios de clases/plantillas web por esta implementación.

## Ajuste de acceso — 2026-10-20

En mobile/lib/main.dart retirar estado/campos/envío de signup. Botón de registro abre /accounts/signup/ del mismo backend, ruta allauth ya usada por el login web. Mantener login, MFA y recuperación. Verificar ausencia del formulario móvil y texto que explica cuenta compartida. No rediseñar a partir de una referencia aún inaccesible.

## Plan de adaptación a referencia y cámara dual — 2026-10-20

1. Reorganizar mobile/lib/care.dart en pantallas por función, conservando api.dart y servicios de negocio existentes. Inicio combina resumen de paciente/próxima toma/acciones; Medicinas y Posturas dejan de depender exclusivamente de la ficha. Plan consulta siempre entitlements; Perfil reutiliza cuenta web.
2. Preparar contrato de detección móvil separado de Bearer del nodo fijo: autenticación de sesión, paciente propio, Premium, dispositivo/origen, UUID idempotente, fecha, calidad y postura. Revisar mobile_models.py y migración aditiva para preservar observaciones anteriores. Origen simultáneo no debe duplicar alerta ni aparentar continuidad de cámara.
3. Integración nativa MediaPipe por canal Flutter en mobile/android/ y mobile/ios/, módulo Dart específico para cámara y captura de resultados. Evaluar compatibilidad oficial/versiones antes de añadir dependencias, modelos y permisos. Nunca enviar fotogramas al backend.
4. Mantener edge/ para cámara fija; extender API/pantalla de monitoreo para distinguir ambas fuentes. No duplicar token de nodo en almacenamiento móvil.
5. Pruebas de permisos denegados/revocación, pausa/resume, varias personas/oclusión, timestamps, fuentes simultáneas, plan expirado y paciente ajeno. Probar por separado Android/iOS con cámara y nodo fijo. SDK temporal ausente y espacio de disco son límites actuales de compilación.
6. Campos adicionales de paciente (dependencia/movilidad/foto), reportes y mediciones del prototipo requieren contrato/migración/métricas definidos; no derivarlos de texto libre ni fingir disponibilidad.

El trabajo de detección dual es ampliación funcional: esta fase actualiza Markdown; la siguiente instrucción explícita de implementación habilita su código según AGENTS.md. La implementación previa permanece preservada.

## Implementación autorizada — 2026-10-20

Mensaje humano: «realiza los cambios en lo que ya estaba en base a lo que te pedi». Ejecutar adaptación sobre archivos existentes. Tokens visuales: índigo#5057a0, fondo#f6f7fc, blanco#ffffff, texto#252a38, secundario#626778; tipografía de sistema accesible. Inicio presenta paciente/próxima acción; navegación por seis funciones con etiquetas y desplazamiento en anchos pequeños. Se conserva la lógica servidor.

Cámara móvil: vista previa local y análisis puntual iniciado por el cuidador, referencias de postura calibradas durante la sesión, nunca inferencia de inmovilidad a partir de fotos aisladas. Nodo fijo mantiene su propia secuencia continua y alertas. Guardar ambas fuentes diferenciadas; observaciones móviles no generan alertas temporales ni sustituyen al nodo. Procesamiento nativo MediaPipe IMAGE; referencias y landmarks permanecen en memoria, fotograma temporal eliminado al terminar. No afirmar validación clínica ni monitoreo móvil de fondo.
