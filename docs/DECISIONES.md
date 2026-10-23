# Registro de decisiones

## Acuerdos generales de esta base

| ID | Fecha | Decisión | Motivo |
|---|---|---|---|
| D-001 | 2026-09-20 | Reutilizar una base maestra y separar cada producto derivado | Evitar mezclar clientes, requisitos y datos |
| D-002 | 2026-09-20 | Primera fase genera spec, plan y tasks, sin código | Pedido explícito del propietario |
| D-003 | 2026-09-20 | Prompt coordinador o prompts individuales, según preferencia | No obligar a pegar una secuencia completa |
| D-004 | 2026-09-20 | Preguntar solo por decisiones importantes no definidas | Evitar entrevistas sobre requisitos ya claros |
| D-005 | 2026-09-20 | Principios generales separados de reglas técnicas y de negocio | Permitir módulos de distintos dominios |
| D-006 | 2026-09-20 | Separar `common_settings`, `settings` normal y `test_settings` aislado | Evitar leer `.env` o recursos normales antes de aplicar los valores de prueba; confirmado por aprobación de spec 001 |
| D-007 | 2026-09-20 | Exponer `puede_registrar_usuarios` mediante context processor que reutiliza el helper/mixin | Mantener una sola política para acceso directo y enlace Registro; confirmado por aprobación de spec 001 |
| D-008 | 2026-09-20 | Mantener axes y preventconcurrentlogins instalados pero desactivados | Son capacidades opcionales que cada proyecto debe decidir, configurar y probar explícitamente |
| D-009 | 2026-09-20 | Mantener correo de consola/verificación none y gráfico de ejemplo | La política de correo y métricas reales se definen por proyecto; no basta descomentar proveedor ni presentar datos demostrativos como reales |
| D-010 | 2026-09-22 | Usar Tailwind 4.3.0 mediante el binario standalone de django-tailwind 4.5.0, sin Node.js | Reduce dependencias del entorno; sustituye la elección técnica de Tailwind 3/npm de la spec 001. La configuración pasa de `tailwind.config.js` a CSS con `@source`; plugins npm futuros requieren reevaluar esta decisión |

Estas decisiones expresan el flujo solicitado. No aprueban ningún módulo de ejemplo.

## Renovación de esta copia — spec 002

| ID | Fecha | Decisión / propuesta | Estado y consecuencias |
|---|---|---|---|
| D-011 | 2026-10-02 | Crear una segunda identidad visual reutilizable sobre las capacidades existentes de Base-2 | Objetivo pedido por el propietario; registrado en spec 002. No crea módulo de negocio ni autoriza código en la fase inicial |
| D-012 | 2026-10-02 | Centralizar colores mediante tokens CSS semánticos y puente Tailwind; gráfico y widgets consumen el mismo contrato | Autorizada con alcance completo de 002 e implementada. Tres paletas y contraste comprobados. Conserva D-010; guía en PERSONALIZACION_VISUAL.md |
| D-013 | 2026-10-02 | Espacio de trabajo claro con navegación compacta, tipografía del sistema y petróleo inicial; probar ciruela/cobre | Implementación autorizada; aceptación estética pendiente. Alternativas verificadas y petróleo restituido. Sin marca comercial ficticia ni fuente remota |
| D-014 | 2026-10-02 | Mejorar movimiento/foco y alinear controles de gestión con el helper de permisos actual | Autorizada e implementada; conserva controles del servidor y D-007. Regresión por URL/CSRF/roles OK. Zoom real y preferencia reducida activada en navegador pendientes |

No se sustituyen D-001 a D-010. Se conserva el gráfico demostrativo de D-009. D-002 se cumplió: el propietario revisó los documentos y dio instrucción posterior explícita de implementación del alcance completo. No autoriza producción, despliegue, commit ni push.

## Modo visual por usuario — spec 003, implementación autorizada

| ID | Fecha | Decisión / propuesta | Estado y consecuencias |
|---|---|---|---|
| D-015 | 2026-10-02 | Documentar por separado el nuevo botón sol/luna con elección persistente por cuenta | Amplía una exclusión de 002 sin cambiar su alcance histórico. D-002 cumplida: propietario revisó documentos y dio instrucción posterior explícita para el alcance completo de 003 |
| D-016 | 2026-10-02 | UserVisualPreference dentro de UsuarioApp, POST propio con CSRF, modo inicial en HTML y pares de tokens claros/oscuros | Autorizada con 003 e implementada. Evita Profile.save/fotos, funciona sin perfil y sin scripts. CreateModel único/check, sin backfill, probado/revertido solo en SQLite efímero. No aplicación real; rollback elimina elecciones; aceptación pendiente |

Se conservan D-001 a D-014. Persistencia solo en navegador no satisface varias sesiones/dispositivos; campo en Profile podía activar fotos y excluía perfiles ausentes. Las tres marcas/ambos modos fueron comprobados; hover oscuro aclarado y QR sobre blanco tras medir/inspeccionar. Revisión estética del propietario pendiente.

## Gestión de cuentas — spec 004, implementación autorizada

| ID | Fecha | Decisión / propuesta | Estado y consecuencias |
|---|---|---|---|
| D-017 | 2026-10-02 | Ampliar UsuarioApp con restablecimiento administrativo sin correo y jerarquía por destinatario | Revisada y autorizada por instrucción posterior del alcance completo de 004; implementada con formulario manual/reconfirmación/Django. Sin migración ni cambios a recuperación de correo/MFA/registro. ZIP solo guía; 57 tests y navegador parcial, aceptación pendiente |
| D-018 | 2026-10-02 | ADMIN gestiona MANAGER/RESTRICTED; MANAGER solo RESTRICTED, tanto al activar como desactivar | Desactivación pedida; activación confirmada expresamente por el propietario (P-004-02). Sustituye la política de esas acciones conservada/verificada en 002, sin modificar su evidencia histórica ni los permisos globales de Registro |
| D-019 | 2026-10-02 | Exigir cargo incluso al superusuario para las acciones administrativas de 004 | **Confirmada por el propietario en P-004-01**: ADMIN para restablecer y ADMIN/MANAGER para gestionar inferiores. Se descarta conservar excepción de actor sin cargo en esos endpoints; helper global/Registro y demás vistas conservan su contrato |

No se sustituyen D-001 a D-016 fuera de las acciones indicadas. D-002 cumplida: documentación primero y después instrucción explícita del propietario para el alcance completo. Protección de destinatarios/formulario aprobados con ese alcance, sin deducir aprobación automática. Ninguna decisión crítica nueva ni cambio de dependencias/esquema. La prueba MFA se aisló por efecto lateral de allauth desactivado, descrito en validation.md, sin activar socialaccount.

## Auditoría y dependencias — 005, propuesta

| ID | Fecha | Decisión / propuesta | Estado y consecuencias |
|---|---|---|---|
| D-020 | 2026-10-02 | Revisar independientemente toda la base implementada con validar-produccion-sdd | Pedida por el propietario, ejecutada con datos sintéticos; informe con bloqueadores. No autoriza correcciones funcionales ni aceptación/despliegue |
| D-021 | 2026-10-02 | Proponer Django 5.2 LTS, paquetes compatibles, scripts fijos/integridad y mantenimiento reproducible | Propuesta de 005; no implementada/autorizada todavía. Conserva capacidades y reglas 001–004; no arregla Registro/perfil por inferencia |
| D-022 | 2026-10-02 | Exponer efectos de datos de allauth antes de actualizar | P-005-01 pendiente del propietario: minúsculas/principales/constraints con backfills no reversibles automáticamente. No operar DB real ni asumir aceptación; detalle en spec/plan 005 |

No se sustituyen D-008/009/010/018/019. Actualizar librerías no activa opciones ni redefine permisos. La asignación de cargos y atomicidad del alta necesitan un alcance funcional propio si se autoriza su corrección.

## Agregar decisiones posteriores

Agregar el siguiente ID libre, fecha real, contexto, alternativas relevantes, decisión, quién la confirmó, specs afectadas y consecuencias. Si todavía es propuesta, marcarla como tal. Si reemplaza otra decisión, indicar cuál y conservar la anterior como histórica.

No modificar silenciosamente el requisito para hacerlo coincidir con un bug.

## Correcciones autorizadas después de auditoría — 2026-10-02

| ID | Decisión | Confirmación y efecto |
|---|---|---|
| D-023 | Aplicar 005, Django 5.2 LTS y lock/hashes, conservando opcionales comentados | Instrucción posterior del propietario «te autorizo a aplicar las correcciones de la validación»; confirma D-008. D-021 pasa de propuesta a implementada. P-005-01 confirmada expresamente para minúsculas/principales y ensayo/recuperación; sustituye su estado pendiente D-022, sin autorizar DB real |
| D-024 | Registro por cargo: ADMIN solo inferiores, MANAGER RESTRICTED, únicamente root con ADMIN asigna ADMIN | Respuesta explícita P-006-01 y posterior autorización de 006 tras spec/plan/tasks. Sustituye excepción root/filtro pk=1 de 001 solo en Registro y su menú; D-018/019 de activar/desactivar/reset intactas |
| D-025 | User/Profile transaccionales y fotos preparadas antes, compensación y borrado posterior al commit | Alcance RF-006-03/04 aprobado con 006; probado en storage local. Sin migraciones. Fallo de limpieza posterior conserva referencia válida y registra error, mantenimiento manual documentado |

No reemplaza decisiones de otros proyectos ni configura hosting/correo/cifrado/auditoría por inferencia. Todo probado con datos ficticios y cambios sin commit/push. Aceptación del propietario pendiente.

## PlanesApp — DOCUMENTAR 007, 2026-10-06

| ID | Decisión / propuesta | Fuente, estado y efecto |
|---|---|---|
| D-026 | Nueva app solicitada PlanesApp; registro público con Google y correo/contraseña, altas automáticamente RESTRICTED | Pedido y respuesta explícita del propietario. Documentado, sin autorización de código. Propone sustituir RF-001-02 solo en este producto, conservando historia y política interna 004/006 |
| D-027 | Usar Vigía Free/Plus/Pro/Hogar con precios/beneficios de capturas | Respuesta explícita. Capturas no son mandato de diseño ni autorización de servicios de vigilancia. Moneda CLP/Free inicial son precisiones propuestas; marca definitiva por definir |
| D-028 | Mensualidad simulada, cambio inmediato sin prorrateo y cancelación al finalizar período | Confirmado expresamente. Reinicio de fechas, descenso a Free y demostración de renovación mediante botón son propuestas detalladas en spec/plan, no confirmaciones atribuidas |
| D-029 | Confirmar correo antes de contratar y probarlo localmente; Google usa correo verificado del proveedor | Confirmado expresamente. Propuesta: allauth verificación optional más gate obligatorio de contratación, para preservar login/MFA internos. Amplía none de D-009 solo para este derivado; mantiene consola/local sin SMTP de producción |
| D-030 | Mantener diseño actual y usar frontend-design; una tarjeta interactiva de prueba con giro al CVC | Pedido explícito. Plan visual documentado con tokens existentes; pagos locales simulados y lista cerrada, sin PAN/CVC persistidos ni pasarela real. No código/UI creados |
| D-031 | Proteger Inicio/listado frente a clientes y filtrar todos los objetos por titular; Google coincidente exige conexión explícita | Propuesta técnica para revisar al abrir registro, fundada en código real. Root conserva helper general para lectura interna; 004/006 no cambian. Sin aprobación de implementación ni cambio efectivo de permisos |

Se mantiene D-002: las confirmaciones de requisitos no son la instrucción posterior para implementar. [Spec](../specs/007-planes-app/spec.md), [plan](../specs/007-planes-app/plan.md), [tareas](../specs/007-planes-app/tasks.md). Producción/pagos reales/migraciones reales fuera de autorización.

## Implementación posterior de 007 — 2026-10-06

| ID | Decisión | Fuente y efecto |
|---|---|---|
| D-032 | Implementar todo el alcance documentado de 007 y usar .venv en esta copia | Instrucción explícita posterior del propietario. Sustituye el estado «sin código autorizado/propuesta» de D-026–031: precisiones técnicas incluidas, 117 tests y evidencia visual parcial; aceptación/OAuth real pendientes. No autoriza DB real/despliegue |

D-026–031 conservan la fuente/estado inicial de DOCUMENTAR; el estado vigente es D-032 y [validation.md](../specs/007-planes-app/validation.md). RF-001-02 y lectura Home/listado sustituidos solo en este derivado; jerarquía 004/006 intacta. .venv reparado en su ruta y lock regenerado desde fuente; no actualización general de dependencias.

## Dashboard y navegación — DOCUMENTAR 008, 2026-10-06

| ID | Decisión / propuesta | Fuente y estado |
|---|---|---|
| D-033 | Seis SVG coherentes con el menú, Inicio oculto a clientes y selector con los mismos sol/luna de Inicio | Pedido explícito posterior a 007. Documentado en 008; no código en esta fase. Root conserva excepción lectora del helper vigente |
| D-034 | Ampliar Home con agregados de suscripciones y volumen mensual simulado, conservando accesos recientes | Pedido de dashboard para ADMIN/MANAGER; indicadores/población/disposición son propuesta técnica concreta, no confirmación atribuida al propietario. Lectura global agregada, sin acceso a métodos/historial ajenos ni permisos nuevos de escritura |
| D-035 | Evolución transversal 008 en apps existentes, con spec→plan→tasks antes de código | AGENTS.md/prompts y número libre comprobado. D-032 sigue vigente para 007; implementación posterior de 008 pendiente. Sin modelos/migraciones/dependencias nuevas previstas |

[Spec](../specs/008-dashboard-navegacion/spec.md), [plan](../specs/008-dashboard-navegacion/plan.md), [tareas](../specs/008-dashboard-navegacion/tasks.md). Estas propuestas no sustituyen las reglas comerciales de D-026–032 ni la gestión 004/006.

## Autorización y ejecución posterior de 008 — 2026-10-06

| ID | Decisión | Fuente y efecto |
|---|---|---|
| D-036 | Implementar el alcance completo de 008 tras entregar spec/plan/tasks | Instrucción posterior explícita «implementa specs 8 Dashboard de suscripciones y navegación coherente alcance completo». Sustituye solo el estado pendiente/propuesto de D-033–035; no altera 004/006/007 ni autoriza datos reales/despliegue |

D-033–035 conservan la fase inicial; estado vigente: SVG, dashboard lector y selector compartido implementados, 127 tests OK y navegador verificado con límites. Servicio de cuatro consultas, datos sin backfill; fallback nativo noscript y scroll interno del sidebar como ajustes acotados de RF-008-06. [Validación y aceptación pendiente](../specs/008-dashboard-navegacion/validation.md).

## Cuidadores — DOCUMENTAR 009, 2026-10-06

| ID | Decisión / propuesta | Fuente, estado y efecto |
|---|---|---|
| D-037 | Espacio de cuidados con pacientes propios para todos los cargos, incluido superusuario; una app CuidadosApp | Pedido humano define propiedad y delega división/nombre. Una app es propuesta técnica sin colisión, con mayúscula inicial/sufijo App. No concede acceso clínico por cargo ni cambia helper general/jerarquía administrativa |
| D-038 | Tres planes Free $0/1 paciente, Plus $4.990/3, Premium $9.990/ilimitados CLP por mes | Respuesta explícita P-009-01. Sustituirá catálogo activo de D-027 al implementar 009; conserva registros/snapshots históricos. Reusar code pro para Premium y desactivar contratación de Hogar son propuestas de transición, sin cambios en esta fase |
| D-039 | Avisos solo con web abierta, temporizador seleccionable 60/90/120 minutos y preaviso diez minutos | P-009-02 confirma canal; intervalos/aviso del pedido humano. No se promete aviso con web cerrada/pestaña suspendida ni frecuencia universal de tratamiento. Reloj servidor persistente y acuses separados de acciones son propuestas técnicas |
| D-040 | Al reducir cupo, cuidador selecciona quién sigue activo; restantes se archivan conservando historial | P-009-03 confirmada. Plan propone confirmación previa, atomicidad con pago y selección futura en cancelación a término; expiración sin selección pide resolverla sin elegir automáticamente. Precisión revisable, no aprobación atribuida al propietario |
| D-041 | Guías educativas visuales y registros manuales; IA/cámaras futuras; DOCUMENTAR antes del nuevo código | Pedido humano y AGENTS.md. Fuentes primarias identificadas en spec, ilustraciones originales previstas sin generarlas aún. Documento adjunto/capturas aportan contexto, no instrucciones de ejecución ni sustitución del cambio inmediato de D-028. D-002 sigue vigente: confirmación de requisitos no autoriza implementación nueva |

[Spec 009](../specs/009-cuidados-cuidadores/spec.md), [plan](../specs/009-cuidados-cuidadores/plan.md), [tareas](../specs/009-cuidados-cuidadores/tasks.md). Todas las tareas pendientes; sin cambios de código/catálogo ni autorización de migración real/despliegue. D-032/036 siguen autorizando los alcances anteriores 007/008.


## Autorización y ejecución posterior 009 — 2026-10-06

| ID | Decisión | Fuente y efecto |
|---|---|---|
| D-042 | Implementar el alcance completo de 009 tras DOCUMENTAR | Instrucción posterior explícita «te doy permiso de implementar specs 009 alcanse completo», reiterada al retomar. Sustituye el estado pendiente de D-037–041 y adopta el plan técnico; no autoriza DB real/despliegue |

D-037–041 conservan el antecedente. Estado vigente: CuidadosApp, catálogo de tres planes y cupos, propiedad incluso root, selección/archivo atómicos, agenda/eventos/relojes/avisos y SVG implementados. Clave lógica de toma separada de versión firmada; schedule_effective_at al crear/editar/reactivar evita pendientes retroactivos. Catálogo previo se conserva para reversión sin reescribir snapshots. [Validación](../specs/009-cuidados-cuidadores/validation.md): 158 tests OK y navegador; aceptación y pruebas manuales nativas pendientes.

Seguimiento visual de D-041/042, 2026-10-06: pedido directo «puedes mejorar las imágenes» autoriza T-009-14 dentro de RF-009-05/11. Serie PNG original generada con image_gen; selección en presentación preserva datos/rutas originales y referencias educativas. No ampliación clínica ni migración real. [Prompts/asignación](../specs/009-cuidados-cuidadores/evidencia/prompts-imagenes-v2.json) y [validación actual](../specs/009-cuidados-cuidadores/validation.md).


## Aplicación móvil — DOCUMENTAR 010, 2026-10-19

| ID | Decisión o propuesta | Fuente y estado |
|---|---|---|
| D-043 | Preparar aplicación móvil a partir de esta base y el informe | Solicitud humana; fase documental exigida por AGENTS/constitución; no autoriza todavía código |
| D-044 | Flutter/Android inicial y suscripciones en portal existente | Referencia del informe, secciones Solución tecnológica y HU-07; propuesta 010, sin reconstruir portal/autenticación |
| D-045 | Reutilizar Django y servicios 009 mediante API; no migrar automáticamente a React/microservicios/NoSQL | Propuesta técnica para compatibilidad, diferencia con arquitectura del informe registrada; pendiente de revisión |
| D-046 | Alcance colaborativo/Edge pendiente de respuesta; no conceder derechos clínicos por cargo | P-010-01/02 consultadas. D-037/propiedad de 009 vigente hasta decisión explícita y cambio autorizado |


## Aclaración de alcance móvil — 2026-10-19

| ID | Decisión o propuesta | Fuente y efecto |
|---|---|---|
| D-047 | Flutter para iOS y Android desde el alcance actual | Instrucción humana explícita. Sustituye limitación Android inicial de D-044; conserva gestión comercial web propuesta |
| D-048 | Incluir detección de posición con MediaPipe | Instrucción humana explícita. Sustituye carácter opcional de detección de D-046; ubicación/hardware/reglas pendientes, nodo local propuesto conforme al informe |
| D-049 | Aplicación habilitada por funciones de cada plan | Instrucción humana explícita. RF-010-11 exige control servidor/UI. Asignación Premium para MediaPipe y recordatorios móviles en todos los planes es propuesta P-010-06 basada en catálogo 0004; no aprobada. Precios/cupos vigentes preservados |

D-044/046 permanecen como antecedentes. No equivale a autorizar implementación. MediaPipe entrega landmarks; clasificación de postura y riesgos necesitan desarrollo y validación propios, según [referencia oficial](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker).


## Aplicación móvil — actualización 2026-10-19

010, 2026-10-19: autorización posterior permite implementar. Reutilizar Django/allauth/services y no sustituir por React/NoSQL del informe. Flutter consume X-Session-Token, capacidades server-side y nodo local autenticado con credencial independiente. Premium habilita detector; Free/Plus conservan manual. Piloto con un nodo activo por paciente; observaciones separadas de CareEvent. Sin colaboración implícita. Sin datos reales ni migración de DB existente. Firma Apple, OAuth/push y precisión real pendientes.


### Referencia AI Studio revisada — 2026-10-20

Acceso resuelto y prototipo inspeccionado. Usuario confirma planes de la web (Free/Plus/Premium,1/3/ilimitados) y MediaPipe tanto en teléfono como en nodo fijo. Registro web/login móvil compartidos. [Mapa y límites](../specs/010-aplicacion-movil/referencia-ai-studio.md); spec/plan/tasks010 ampliados, tareas18–23 pendientes. No se afirma que el diseño o la cámara móvil ya estén implementados.

## D-011-01 — Propuesta22/10/2026

Conservar backend y cuentas de007/010: RAR es referencia anterior, no reemplazo. Proponer reloj independiente sin fabricar CareEvent; un aviso local por vencimiento, con permisos y reconciliación. Proponer traslado físico web/ y separación de funciones Flutter, conservando datos/labels/migraciones. Diseño móvil se preserva por aceptación expresa; web adopta sus tokens. Android e iPhone confirmados por usuario. Decisiones técnicas pendientes de instrucción posterior de implementación; servidor/firma externa no inventados.

## D-011-02 — Alcance de plataforma, 2026-10-22

El propietario fija el entorno del proyecto: Windows, **Android primero, iOS fuera de alcance**. Sustituye la parte iOS/iPhone de D-011-01 y de RF-011-01, RF-011-03 y la aceptación 2/6 de la [spec 011](../specs/011-ecosistema-instalable/spec.md). T-011-10 pasa a fuera de alcance; su ID se conserva. El código iOS existente (carpeta `mobile/ios`, plugin `vigia_pose`) no se elimina ni se mantiene activamente: no se compila, prueba ni declara entregado. Reincorporar iOS requiere una nueva decisión explícita.
