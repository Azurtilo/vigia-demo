# Plan técnico — 009 / CuidadosApp para cuidadores

Spec: [spec.md](spec.md). Estado: implementación ejecutada y validación técnica completa; revisión manual/aceptación pendientes.
Autorización posterior explícita: «te doy permiso de implementar specs 009 alcanse completo». El diseño técnico siguiente conserva la propuesta inicial y sus decisiones; los archivos ya existen. No incluye migrar la DB existente ni desplegar.
Decisiones P-009-01/02/03 confirmadas; aceptar documentos no autoriza migraciones reales ni despliegue.

## Inspección e integración real

Leídos constitución, README/proyecto/estado/índice, specs 007/008, arquitectura/decisiones/observaciones y guía visual; archivo del propietario e imagen como contexto. Siguiente libre 009 y ausencia de CuidadosApp comprobados. Estado Git inspeccionado; implementación existente 007/008 y archivos del propietario preservados. No se lee .env/DB/media personal ni se ejecuta Django durante DOCUMENTAR.

LOCAL_APPS real en core/common_settings.py, settings normal lo reutiliza; core/urls.py es raíz. PlanesApp tiene Plan/beneficios, Subscription uno a uno con snapshots y fechas, métodos/operaciones ficticios. services.summary mantiene plan contratado si venció sin cancelación; no usar simplemente su is_paid para conceder capacidad vigente. execute bloquea User y Subscription y conserva idempotencia. Reutilizar transacciones/cálculos, sin reemplazar pagos ni allauth.

Home solo expone datos comerciales a ADMIN/MANAGER/root y redirige clientes a Mi suscripción; en 009 el cliente debe ir al panel de cuidados. Los pacientes nunca se consultan desde el dashboard global 008. ClientMixin de PlanesApp protege autenticación/actividad y exige correo solo donde corresponde al pago; CuidadosApp necesita autenticación/actividad y propietario, no PermitsPositionMixin ni un nuevo cargo.

## Organización propuesta

Una **CuidadosApp**: pacientes, medicamentos, horarios/tareas, guías, eventos, relojes y acuses comparten paciente/titular y transacciones. Separar responsabilidades en servicios de capacidad, cuidados y agenda cuando lo requiera la complejidad; no crear una app por tabla ni un framework de plugins. PlanesApp conserva catálogo/compra y expone capacidad resuelta por fechas.

| Área | Archivos propuestos nuevos | Archivos reales a integrar |
|---|---|---|
| App/registro y rutas | CuidadosApp/apps.py, models.py, urls.py, views.py, forms.py, permissions.py | core/common_settings.py, core/urls.py |
| Propiedad/cuota/transacciones | CuidadosApp/services.py, scheduling.py; módulos más pequeños si facilitan reglas | PlanesApp/models.py, services.py/forms.py/views.py, tests.py |
| Guías y contenido | CuidadosApp/migrations para catálogo educativo; templates/pages/CuidadosApp y components/CuidadosApp; static locales de app | Layouts/guía visual actuales; sin modelos sensibles expuestos en admin |
| Recordatorios y relojes | CuidadosApp/static/CuidadosApp/care.js y care.css; endpoints privados | theme/static_src/src/styles.css @source/exclusiones, shared nav y selector |
| Entrada/UI | Plantillas de panel, pacientes, ficha, medicamentos, agenda, guías, registro y selección de activos | homeApp/views.py, navbar/nav.html, components/visual_mode.html, PlanesApp checkout/cancelar/mi_suscripcion |
| Pruebas | CuidadosApp/tests de propiedad, cuota, agenda y registro | UsuarioApp/homeApp/PlanesApp regresión aislada |

Todos estos archivos son propuestas; no existen por aparecer aquí. Nombre CuidadosApp delegado y validado. Extiende components/Layout/base_extendido.html/content_main y base_pages.html/content_pages cuando corresponda, conservando csrf/crispy/errors/tokens.

## Modelos propuestos

- Patient: FK owner a User, campos de ficha de spec, active/archived_at, created/updated y versión. Propiedad inmutable desde sesión; archive por POST. No almacenar imagen del paciente ni identificador nacional.
- Medication: FK Patient, nombre/dosis/notas, active, start/end dates, versión; MedicationTime para horas diarias únicas por medicamento. Formularios restringen paciente a propios activos; edición conserva snapshots de eventos anteriores.
- CareTask: FK Patient, nombre/notas, horario diario opcional, estado y rango de fechas. Sin horario se realiza manualmente y no genera alarma inventada.
- CareGuide: código/título/categoría, instrucciones educativas/precauciones, asset local/alt, fuente/version y active. Biblioteca global de referencia, sin datos de pacientes.
- PostureTimer: OneToOne Patient, último evento de posición, intervalo restringido 60/90/120, next_due_at aware, paused y generation/version. FK de último evento nullable para estado inicial «Sin registro».
- CareEvent: FK Patient/autor, referencia/idempotencia, kind postura/medicamento/cuidado/corrección, fecha servidor, occurrence_key y snapshots de nombre/dosis/posición/intervalo; vínculo al evento corregido. Tipo exige campos coherentes. Registro/corrección no es acuse de aviso.
- ReminderReceipt: usuario/paciente, clave de ocurrencia/generación/tipo, instante/estado visto; unique impide dos avisos de la misma ocurrencia. Datos filtrados por titular.
- CapacitySelection: selección propia para reducción inmediata o fecha de término, vinculada a suscripción/versión, paciente(s) elegidos y effective_at. No usar IDs sin validar dueño ni decidir una selección automática.

No aplicar cambios a Profile para gestionar cuidados. Resolver índices por owner/active, patient/date, due y ocurrencia; constraints de intervalo/fechas/unicidad. Revisar borrado/cascadas del administrador de cuentas para no revelar fichas de salud ni destruir historial por una acción genérica: modelos sensibles sin registro público de Django Admin, mensajes sin datos clínicos y protección de eliminación donde haga falta.

## Catálogo, capacidad y transición

Propuesta conservadora: reutilizar códigos `free`, `plus`, `pro`; **pro pasa a nombre visible VIGIA Premium**. Añadir a Plan `max_active_patients` nullable (null ilimitados, positivos para límites), asignar 1/3/null. Tres planes activos, $0/$4.990/$9.990 CLP; actualizar beneficios a cuidados. Mantener Hogar como fila histórica inactiva, sin borrar FK, conservar snapshots y período; cupo transitorio ilimitado para ese período anterior. Mostrar plan anterior/elección explícita de plan vigente, no renovación de un plan inactivo ni migración automática de dinero.

No editar 0002_catalogo_inicial retroactivamente. Nueva migración PlanesApp para campo/catálogo, reversible con valores anteriores o respaldo de filas afectadas, sin tocar SimulatedOperation ni snapshots de Subscription. CuidadosApp 0001 depende de esa migración y AUTH_USER_MODEL; no crear dependencias circulares. El plan vigente se calcula en servidor desde fechas, cancelación y snapshot del período, distinto de mostrar estado comercial Vencida. Free virtual para cuentas sin suscripción, sin crear fila al leer.

Alta/reactivación: atomic y bloqueo de User, como los servicios de pago actuales, luego revisar suscripción/capacidad y contar activos efectivos propios. Una selección futura ya efectiva gobierna elegibilidad y cuota aunque todavía no se haya materializado Patient.active por POST; usar el mismo cálculo en listas, acciones y avisos. Así se serializan dos altas y un cambio de plan para el mismo cuidador. SQLite tests prueban lógica/constraints, no afirman bloqueos PostgreSQL.

Si hay reducción inmediata: formulario solicita pacientes a conservar, firma IDs/actor/versión de suscripción y conjunto de activos; checkout muestra cuáles quedan archivados. Validar selección/propiedad/cantidad y estado actual antes de aplicar; pago rechazado no altera pacientes. Al aprobar, suscripción/selección/archivos/relojes se actualizan juntos, idempotentemente. Renovar token si hubo altas/archivos/cambio de suscripción concurrentes, sin continuar con una selección vieja.

Cancelación al cierre: guardar selección efectiva futura en el mismo POST de cancelación; seguir cuidando todos durante vigencia. Permitir actualizar selección propia antes de end; retirar cancelación invalida selección futura. Si llega end, los seleccionados continúan y los otros son archivados efectivos; GET calcula elegibilidad sin materializar escritura. Primer POST autorizado materializa transición atómica. Si no existe selección válida al vencer, pedirla claramente y conservar fichas/historial de lectura antes de habilitar acciones/avisos; no seleccionar ni borrar por orden. Es precisión técnica propuesta, visible en UI. No reiniciar reloj de un paciente conservado; al reactivar uno archivado, el cuidador inicia nuevamente sus recordatorios, no se disparan atrasos históricos en masa.

## Agenda y temporizadores

Servidor proporciona now y vencimientos UTC; UI interpreta deltas, nunca asigna next_due basado en Date.now del dispositivo. Primer registro de postura inicia reloj; elección de intervalo informa consecuencias. Nueva postura/intervalo/pausa usa generation y bloqueo/versionado, y desactiva acuses previos de ese reloj sin borrar historial. Reanudar no crea postura realizada.

Medicamentos/tareas iniciales a horas diarias locales, con rangos de fechas. Agenda deriva ocurrencias para el día/pendientes recientes desde horarios y eventos; no guardar cumplimiento por GET. La clave lógica estable de ocurrencia incorpora objeto/fecha-hora; el token de acción firmado incorpora paciente/objeto/versión/fecha-hora. Así se rechaza un formulario obsoleto sin reabrir una toma registrada al editar dosis. Editar horario afecta próximas ocurrencias según confirmación; eventos ya registrados conservan dosis/horario aplicados. No reconstruir incumplimiento histórico no observado como un hecho clínico.

DST: guardar instantes aware en UTC; horarios diarios se anclan a America/Santiago. En hora inexistente mostrar ajuste al primer instante válido; en hora repetida crear una sola ocurrencia con fold definido, mostrando fecha/hora. Probar ambos casos y ventanas de medianoche; no emitir duplicados por cambio de día.

Canal confirmado: **solo web abierta**, panel/banner de próximas acciones y avisos accesibles. Poll privado acotado (propuesta 30 s) y contador local basado en respuesta del servidor; revalidar al volver a pestaña/conexión. Preaviso en ventana últimos diez minutos, vencimiento/atraso después. No garantizar latencia exacta cuando navegador suspende recursos. Sin push, correo/SMS, service worker, cron/Celery ni permisos de notificaciones del dispositivo para este alcance.

Para dos pestañas, reclamar aviso por POST/CSRF con recibo único; solo el ganador anuncia la ocurrencia. Repetir entrega de solicitud no crea doble evento. Vistos no se repiten; atrasos se muestran en agenda aunque se haya acusado aviso. Si se vuelve después de suspensión, mostrar estado actual, no una ráfaga de todos los avisos viejos. Nueva generación invalida reclamos de reloj anterior. GET/poll solo lectura; peticiones limitadas al usuario y pacientes elegibles.

## Permisos y rutas propuestas

Namespace `/cuidados/`, rutas de panel, lista/alta, ficha/editar/archivar/reactivar, medicamentos/horarios, tareas, guías, agenda/historial, registrar acciones, configuración/pausa/reanudar reloj, selección de activos y avisos/acuse. Vistas por clases; escrituras solo POST con CSRF, propietarios en querysets y autorización común antes de lookup hijo. No APIs globales por cargo ni `owner` recibido. Respuestas de fichas/agendas privadas no cacheables; payload mínimo, no datos clínicos en logs/storage del navegador/URLs externas.

Anónimos login; inactivos denegados; todos activos gestionan propios incluso root o sin Profile. Sidebar añade Cuidados/Pacientes/Agenda/Guías para activos; Inicio administrativo sigue su flag. Home redirige clientes al panel, no a una suscripción comercial. Selector actual retorna Home: clientes terminan en panel por esa redirección, sin nuevo next abierto. Verificación de correo de contratación y cargos 004/006 permanecen.

## Diseño con frontend-design

Seguir la base vigente, no imitar folleto pastel. Tokens de referencia: petróleo #0f766e, petróleo claro #5eead4, fondo claro #f2f5f8, superficie #ffffff, tinta #182536 y fondo oscuro #101923; usar variables semánticas. Segoe UI/--font-ui, título 28–32, sección 20, texto 16 y ayuda 14; tiempos tabulares, instrucciones de menos de 80 caracteres por línea cuando posible.

Foco de la pantalla: **la próxima acción por paciente**, con nombre, postura actual, tiempo restante y acción «Registrar cambio». No panel comercial con cifra grande ni docenas de tarjetas iguales. Desktop agenda ancha a la izquierda y paciente seleccionado/guía visual a la derecha; móvil una columna en orden urgencia→acción→guía→historial. Pacientes distinguibles por nombre/avatar genérico, sin depender solo de color.

```text
Mis cuidados                           Mi suscripción / modo
Próximas acciones: paciente, tarea y tiempo     Ficha elegida
Agenda de hoy con filtros propios              Postura e ilustración
Registrar cambio / medicamento / cuidado       Guía / instrucciones
Historial reciente del paciente seleccionado
```

Ilustraciones originales SVG locales para posiciones, diagramas discretos coherentes con instrucciones y alt; no crear imágenes en DOCUMENTAR. Guías educativas con fuente/versión y límites concretos, sin prometer validación clínica. IA/cámaras como bloque futuro sin CTA operativa. Cambios de estado/respuesta a acción con movimiento breve, respetar prefers-reduced-motion. Evitar cuenta regresiva que se anuncie cada segundo a lectores de pantalla; aria-live para transición/aviso, navegación y confirmación accesibles.

Revisión del brief: se concentra el énfasis en acción/tiempo por paciente y una ilustración educativa, manteniendo chrome/paleta actual; se descartan colores o íconos infantiles copiados del folleto y analítica clínica inventada. Ninguna fuente remota o paquete gráfico nuevo requerido.

## Pruebas, migraciones y reversión

Tras autorización: .venv y core.test_settings; nueva suite `manage.py test UsuarioApp homeApp PlanesApp CuidadosApp --settings=core.test_settings`, check/esquema y `tailwind --settings=core.test_settings build`. Registrar @source de CuidadosApp con exclusiones migraciones/cachés/dependencias. Tests de propiedad con cada cargo/root/sin perfil e IDs anidados, límites concurrentes, selección/rollback/idempotencia de plan y archivo, historia/snapshots, pausas/generaciones y DST.

Navegador: dos cuidadores, planes/cupos, reducción/cancelación y retiro, archivo/reactivación, guías/agenda, registrar postura/medicamento, límites de 10 min/vencimiento con reloj de prueba del servidor, recarga/two tabs/suspensión, claro/oscuro/móvil/teclado/reducido/sin JS. Sin JS, formularios/guías/agenda operativos; contador/poll automático no opera, indicar actualización manual. No simular haber registrado una acción por aviso.

Migraciones solo ensayadas con fixtures y reversión en DB efímera; identificar/resguardar y pedir autorización propia antes de base existente. Revertir CuidadosApp elimina tablas/eventos propios: requiere backup de negocio, no un rollback silencioso de datos. Catálogo antiguo/flags conservados en reversión, snapshots comerciales intocables. PlanesApp autenticación/pagos actuales preservados.

Documentar resultados reales por RF en validation.md después de ejecutar, nunca reutilizar los 127 tests de 008 como cobertura del cuidado. La primera fase documental terminó con Markdown; autorización y ejecución posteriores se registran abajo. No secretos, datos reales, instalación, código, migraciones ejecutadas, commit/push ni despliegue.


## Implementación efectiva y ajustes de integración — 2026-10-06

- CuidadosApp registrada en core/common_settings.py y core/urls.py, con permisos de titular, CBV y 21 rutas. Reglas separadas en capacity.py, services.py y scheduling.py; ningún modelo sensible registrado en admin.
- PlanesApp 0003 incorpora límite y copia del catálogo anterior; 0004 aplica los tres planes/beneficios y conserva Hogar histórico. CuidadosApp 0001 depende de PlanesApp 0004; 0002 incorpora cuatro guías; 0003 añade schedule_effective_at. Avance/reversión/reaplicación ensayados en memoria, nunca en DB existente.
- Patient.owner PROTECT y representación genérica evitan pérdida de historial/divulgación de nombre en borrado administrativo de cuentas. Eventos inmutables mediante flujo público; corrección añade evento vinculado.
- Horarios nuevos/editados/reactivados solo producen actividades desde schedule_effective_at; versiones invalidan tokens anteriores. Clave lógica de dosis estable separada de versión firmada impide duplicación por cambio de texto; agenda realizada usa snapshot aplicado. Historial muestra autor y hora del servidor.
- Cuota y pagos comparten bloqueo de User. GET calcula selección efectiva sin archivo; un POST autorizado materializa la transición. Los formularios de checkout/cancelación/retiro de último método solo permiten pacientes propios, y pago fallido no archiva.
- care.js en base autenticada consulta cada 30 segundos, contador monotónico desde hora servidor, claim POST único y actualización al volver a foco/conexión. Sin storage clínico local. Shared nav/layout/modo existentes conservados; Home cliente→panel de cuidados, interno→agregados comerciales.
- Cuatro SVG locales y plantillas de panel/ficha/agenda/guías/historial/formularios; @source Tailwind de nueva app. Sin dependencia/fuente remota nueva.
- [Validación](validation.md): 158 pruebas, 89 HTML y 13 JPEG; carrera SQLite sobre último cupo y rollback comercial. Zoom/movimiento reducido/offline/suspensión nativos y backend con bloqueos de fila pendientes de comprobación manual; aceptación del propietario pendiente.

## Mejora visual de imágenes — 2026-10-06

Corrección posterior de selectores, T-009-15: override propio en templates/tailwind/layout/select.html, conservando filtros crispy/build_attrs/optgroups/select_option y condición de múltiples. CSS semántico compartido en static/css/styles.css para wrapper relativo, flecha absoluta decorativa 20 px/pointer-events none, color var(--muted), padding reservado y tamaño explícito independiente de utilidades de paquete. Mayor especificidad que regla genérica de SVG de formulario; base.html cambia revisión del CSS. Build standalone y navegador/regresión de base requeridos por componente compartido; no editar site-packages ni ampliar reglas de cuidados.

Pedido directo de reemplazar la calidad de las cuatro ilustraciones. Ajuste acotado de RF-009-05/11, autorizado por el pedido y alcance vigente. Nueva serie bitmap original mediante imagegen, integrada con colores y layout de frontend-design. Se conservan SVG anteriores y rutas/datos de guía como respaldo; se resolverá el asset visual en presentación sin migraciones. Figuras humanas más reconocibles, cama y apoyos legibles; títulos/instrucciones siguen en HTML accesible. Sin ampliar recomendaciones clínicas. Validación visual con fixtures/core.test_settings y navegador; no repetir suite completa por un cambio puramente visual.

Implementado: CareGuide.illustration resuelve únicamente las cuatro rutas SVG iniciales a PNG v2 y alt concordante; imágenes personalizadas conservan su ruta/alt. Componente guide.html compartido en biblioteca/panel/ficha, carga diferida y revisión de caché del asset independiente de la versión clínica. PNG completos copiados desde image_gen, sin transformación posterior. Revisión visual corrigió la asignación de laterales por lado del paciente: cabeza a la derecha de la composición para izquierda apoyada y viceversa, con rostro hacia el observador. 31 pruebas del módulo y cuatro vistas de navegador comprobadas; no clases/CSS/fuentes nuevas, por lo que no requiere recompilar Tailwind.
