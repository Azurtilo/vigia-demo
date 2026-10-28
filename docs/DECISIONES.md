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

El propietario fija el entorno del proyecto: Windows, **Android primero, iOS fuera de alcance**. Sustituye la parte iOS/iPhone de D-011-01 y de RF-011-01, RF-011-03 y la aceptación 2/6 de la [spec 011](../specs/011-ecosistema-instalable/spec.md). T-011-10 pasa a fuera de alcance; su ID se conserva. El código iOS existente (carpeta `mobile/ios`, plugin `vigia_pose`) no se elimina ni se mantiene activamente: no se compila, prueba ni declara entregado. Reincorporar iOS requiere una nueva decisión explícita. **Sustituida por [D-068](#d-068--ios-en-el-alcance-2026-10-26) el 2026-10-26.**

## D-011-03 — Limpieza de estructura, 2026-10-22

El propietario autoriza expresamente una limpieza de estructura sin fase documental previa (spec/plan/tasks), con registro solo en este archivo. No cambia funcionalidad, datos, migraciones ni labels: las apps Django `CuidadosApp`, `PlanesApp`, `UsuarioApp` y `homeApp` **no se renombran** porque sus labels están amarrados a las migraciones. La reorganización previa en `web/`, `mobile/` y `edge/` se registró en un commit base antes de la limpieza.

| Punto | Cambio |
|---|---|
| 1 | `README.md` presenta VIGIA (componentes, entornos por sistema operativo, ejecución, equipo). El contenido de la base Django reutilizable pasa a [BASE_ORIGINAL.md](BASE_ORIGINAL.md). Convención de entornos: Windows usa `.venv` (web) y `.venv-edge-win` (edge); macOS conserva `.venv-mobile` y `.venv-edge`. Cada integrante los crea localmente y nunca se suben al repositorio |
| 2 | Se eliminan los archivos de re-exportación de `mobile/lib/` (`api.dart`, `care.dart`, `phone_pose.dart`, `phone_pose_native.dart`, `phone_pose_web.dart`, `pose_classifier.dart`). Los imports apuntan directamente a `core/` y `features/`. Solo las pruebas los usaban |
| 3 | `.gitignore`: se agregan `.DS_Store`, `.gradle/`, `edge/models/`, `.venv-edge-win/` y los patrones `.work-*/` y `.recovery-*/`, que sustituyen las entradas numeradas. Se quitan las entradas duplicadas o redundantes (`.venv` repetido, `*.pyc`, `web/**/__pycache__/`). `.venv-edge/` y `.venv-mobile/` se conservan. El modelo por defecto de `edge.run` y `edge.smoke` pasa de `/tmp` a `edge/models/pose_landmarker_lite.task` |
| 4 | Revisión con `git ls-files` y el historial completo (`git log --all`): nunca se versionaron `.env`, `db.sqlite3`, `media/` ni `.DS_Store`, así que no hubo `git rm --cached`. Los `.DS_Store` y la caché `.gradle/` del plugin quedaron fuera del commit base |
| 5 | Apps Django sin renombrar (labels amarrados a migraciones) |
| 6 | Verificación final en Windows: check sin problemas, makemigrations --check sin cambios, **173 tests Django OK**, **5 tests Edge OK** (sintéticos), `flutter analyze` sin problemas y **13 tests Flutter OK**. `edge.smoke` no se ejecutó: no hay un entorno Edge de Windows con MediaPipe en esta máquina |

## D-012-02 — Envío desacoplado, riesgos tardíos y avisos sin ventana fija, 2026-10-22

Corrige QA-2026-10-22-01/02. El nodo envía y renueva el lease en un hilo aparte con cola en memoria; el bucle de cuadros solo consulta si el lease está vigente. Se mantiene el fail-closed: el lease vence 15 s después del inicio de la última renovación exitosa o al recibir 401/403, y entonces se detiene la captura. Un fallo de red ya no detiene la captura de inmediato (antes `lease_until = 0`); la demora tolerada queda acotada por el lease. Las observaciones de riesgo pueden llegar con hasta 1 h de antigüedad (antes 2 min, igual que las ordinarias), conservando `observed_at` e `event_id`. El comando de avisos selecciona riesgos por `received_at` en la última hora y sin `PushReceipt`; el recibo, creado solo tras aceptar FCM, deduplica. Alternativa descartada: seguir capturando sin conexión más allá del lease, porque cambia el control de revocación (decisión de privacidad de 010). La cola no persiste si el proceso se reinicia.

## D-012-01 — Regla de caída sobre landmarks de imagen, 2026-10-22

La detección de caídas (spec 012) usa `pose_landmarks` normalizados de imagen, no `pose_world_landmarks`: estos tienen el origen en la cadera y no permiten medir su altura. Las longitudes se normalizan por la longitud del tronco para no depender de la distancia a la cámara. Se elige una regla determinista con umbrales configurables en lugar de un clasificador entrenado, porque no hay datos etiquetados. Una caída puede llegar con postura `indeterminada` (la persona en el suelo no coincide con la calibración de cama); la inmovilidad no. La señal perdida más de `max_gap_seconds` reinicia la regla sin aviso, igual que la inmovilidad. Pendientes: P-012-01 (frecuencia de `send_mobile_reminders` para el objetivo de 10 s) y P-012-02 (ajuste de umbrales tras el protocolo). Resueltos el 2026-10-25 por D-051 y D-053.

## Respuestas del propietario a pendientes 010/012 y QA — 2026-10-25

Fuente: documento «VIGIA — Pendientes por completar» (23-10-2026, commit 4425f1e) con el registro de respuestas completado por el propietario, más respuestas explícitas en la sesión del 2026-10-25 («1A, 2A, 3B, 4 si (0/0/1 nodo), 5 no, 6 si, 7 nada, 8 sí»). Estas decisiones fijan alcance y diseño; **no autorizan código**. Cada una pasa por spec → plan → tareas y requiere una instrucción posterior de implementación.

| ID | Decisión | Sustituye / efecto |
|---|---|---|
| D-050 | **P-010-02 A — cuidado delegado.** Vínculo explícito paciente–usuario con rol `familiar` o `cuidador`, invitación, aceptación y revocación. El familiar configura el plan de cuidados y ve el historial; el cuidador ve la agenda, confirma medicamentos y registra posturas, y `CareEvent.author` registra al cuidador real. Detalle: (a) el cuidador **no ocupa cupo** del plan (el cupo cuenta pacientes); (b) un cuidador **puede atender a pacientes de distintas familias**, con un vínculo por invitación; (c) tras la revocación **no ve nada** del paciente y sus registros anteriores se conservan en el historial con su autoría; (d) en esta versión la invitación es **solo por código**; la invitación por correo queda como trabajo futuro | Sustituye la parte «colaboración pendiente» de D-046 y, al implementarse, la propiedad única de D-037 para los pacientes con vínculos. Se documenta en una spec nueva (013, comprobar número libre) con matriz de permisos por acción y pruebas de acceso denegado por rol |
| D-051 | **P-012-01 A — push de caída inmediato.** Al recibir una caída, el backend envía el push después de guardar (`transaction.on_commit`), con timeout corto para no bloquear la respuesta al nodo y deduplicación por `PushReceipt`. `send_mobile_reminders` queda como reintento | Sustituye la exclusión «envío inmediato de push en la petición del nodo» de la spec 012. La llamada a FCM debe quedar fuera de transacciones con filas bloqueadas (coherente con QA-09). Requiere tareas fechadas en la spec 012 |
| D-052 | **Privacidad (QA-05) A.** Spec de privacidad con consentimiento (versión, fecha, titular o representante), plazo de conservación por tipo de dato, comando de purga, exportación y eliminación de cuenta | Spec nueva (014 o la siguiente libre). La eliminación obliga a revisar los `on_delete=PROTECT` actuales. Cifrado en reposo y procesos formales de la Ley 21.719 se evalúan en esa spec |
| D-053 | **P-012-02 A — ajuste de umbrales con protocolo propio.** Protocolo de caídas simuladas con voluntarios, colchoneta y video autorizado procesado solo en local, más una serie de actividades normales para medir falsos positivos | Requiere consentimiento de los participantes y cámara fija. El denominador de falsos positivos se fija en el protocolo antes de ejecutarlo (propuesta: 20 caídas y 40 actividades normales). Resultados en `specs/012-deteccion-caidas/validation.md` |
| D-054 | **P-010-05 A — Firebase de prueba.** Proyecto Firebase de prueba, credenciales por variable de entorno fuera del repositorio, prueba en un Android físico y tiempos registrados en `validation.md` | Da evidencia real de HU-05 y de la latencia de punta a punta. Ninguna credencial se versiona ni se copia en documentos |
| D-055 | **P-010-06 A — funciones por plan.** Recordatorios móviles en Free, Plus y Premium; detección MediaPipe y alertas automáticas solo en Premium. Nodos incluidos: Free 0, Plus 0, Premium 1 nodo activo por paciente | Confirma la propuesta de D-049 (antes «no aprobada»). Precios y cupos de D-038 sin cambios |
| D-056 | **P-010-04 A — autenticación.** Se aprueba el esquema vigente: `X-Session-Token` de allauth headless para la app y credencial propia con hash para el nodo. Se deben fijar vencimiento de sesión, cierre de sesión remoto y revocación de nodos desde el portal | Sin JWT ni dependencias nuevas. Los valores de vencimiento se proponen en la spec correspondiente; no se inventan aquí |
| D-057 | **P-010-01 / P-010-03 A — captura y Android.** El nodo Edge es la vía principal de detección (como en el informe) y la cámara del teléfono es una alternativa demostrativa. Versión mínima Android 8.0 (API 26) | Cierra la ubicación pendiente de D-048. iOS sigue fuera de alcance (D-011-02) |
| D-058 | **QA-14 A — texto del push de riesgo.** El aviso de caída o inmovilidad muestra un texto genérico (propuesta: «VIGIA: alerta de riesgo, abre la app») con visibilidad privada en la pantalla de bloqueo; el detalle se ve dentro de la app tras iniciar sesión | Precisa RF-012-07 (hoy «Posible caída»). Se mantiene la prioridad alta en Android |
| D-059 | **Política de Git A.** Dentro de una implementación autorizada: rama `feature/NNN-nombre` desde `develop`, un commit por tarea, PR hacia `develop` y nunca push directo a `main` | Formaliza la práctica usada en 012. AGENTS.md actualizado. Merge del PR, push a `main`, despliegues y migraciones reales siguen requiriendo autorización explícita |
| D-060 | **RNF disponibilidad ≥ 99,5 % — B.** Se declara objetivo de diseño **no medido**; el informe describe la arquitectura necesaria (base gestionada, más de una instancia, monitoreo externo de uptime) | Con SQLite en una sola instancia no se mide ni se declara cumplido |

Siguiente paso documental: specs nuevas para D-050 (familiar/cuidador) y D-052 (privacidad), y tareas fechadas en la spec 012 para D-051 y D-058, junto con los hallazgos QA técnicos.

## Respuestas del propietario a la spec 013 — 2026-10-25

Fuente: respuesta explícita en la sesión del 2026-10-25 a las propuestas de la [spec 013](../specs/013-cuidado-delegado/spec.md). Fijan alcance; no autorizan código.

| ID | Decisión | Efecto |
|---|---|---|
| D-061 | **P-013-01** — El familiar invitado puede hacer lo mismo que el titular, salvo archivar pacientes, gestionar el cupo, los nodos y los accesos | Confirma la propuesta. Matriz de la spec 013 sin cambios |
| D-062 | **P-013-02** — El cuidador no ve el historial completo, solo la agenda del día y la última postura | Confirma la propuesta (minimización de datos de salud). RF-013-14 |
| D-063 | **P-013-03** — El push de caída o inmovilidad también llega al cuidador, que suele estar en el domicilio y podría reaccionar antes | Cambia la propuesta inicial (solo titular y familiar). Amplía HU-05, que nombra al familiar. RF-013-11, T-013-09 y la spec 012 (push inmediato, D-051) deben usar estos destinatarios |

## Respuestas del propietario a la spec 014 — 2026-10-25

Fuente: «respecto a p14 me parece todo bien, registralo […] autorizo implementar» (sesión del 2026-10-25). La implementación de T-014-01..10 queda autorizada en `feature/014-privacidad`; no autoriza merge, despliegue ni migración de una base real.

| ID | Decisión | Efecto |
|---|---|---|
| D-064 | **P-014-01** — Plazos de conservación según la tabla de la spec 014 (intentos 24 h, invitaciones 90 días, recibos 30 días, observaciones sin riesgo 30 días y con riesgo 1 año, paciente archivado 2 años) | `PrivacidadApp/retention.py` y comando de purga |
| D-065 | **P-014-02** — Al eliminar la cuenta del titular se eliminan sus pacientes con todos sus datos | `erase_account` usa `delete_patient`; el traspaso a un familiar queda como futuro |
| D-066 | **P-014-03** — Pacientes existentes sin consentimiento: ficha visible, registros nuevos bloqueados hasta registrar el consentimiento | `consent.require` en la elegibilidad de cuidado y en la detección |
| D-067 | **P-014-04** — Texto de la política como borrador del prototipo, pendiente de revisión legal antes de datos reales | Página pública versionada con el aviso |

Consulta del propietario sobre conservar por un tiempo los datos de un paciente eliminado por si se vuelve a registrar: se recomienda no hacerlo. Eliminar es la supresión pedida, y reconocer al «mismo» paciente exigiría volver a vincular datos que se pidió borrar. La vía reversible es **archivar**, que conserva todo por 2 años (D-064) y permite reactivar. La confirmación de eliminación ofrece archivar como alternativa. Una papelera breve con «deshacer» (por ejemplo, 7 días) queda como opción futura si el propietario la pide.

## D-068 — iOS en el alcance, 2026-10-26

Fuente: «prepara la spec con la lista, ademas quiero incluir iOS al alcance» (sesión del 2026-10-26). **Sustituye D-011-02.** VIGIA se entrega en Android e iOS, con Android primero. Las compilaciones y pruebas iOS solo pueden hacerse en macOS con Xcode. El trabajo y la evidencia se documentan en la [spec 015](../specs/015-integracion-unificado/spec.md). T-011-10 conserva su ID y su trabajo pasa a T-015-08..11. Siguen fuera del alcance la publicación en App Store y, salvo que P-015-01 elija la opción B, TestFlight y el push APNs. Respuestas del propietario a P-015-01..04 en la sección siguiente.

## Respuestas del propietario a la spec 015 — 2026-10-26

Fuente: respuesta explícita en la sesión del 2026-10-26 a las propuestas de la [spec 015](../specs/015-integracion-unificado/spec.md), tras revisar la rama `docs/015-integracion-unificado`. Se traen los cuatro grupos de la lista A (A1–A5, A6–A7, A8–A9 y A10–A11) y nada de la lista B (B1–B10): el borrado de `CLAUDE.md`, la sección añadida a `AGENTS.md`, las re-exportaciones eliminadas por D-011-03, los cambios a la spec 011, `.DS_Store`, cachés de Gradle y `.work-025/`, `docs/ORGANIZACION.md`, la guía de instalación con IP fija y contraseña, las evidencias de otra máquina, las diferencias solo de fin de línea en ~230 archivos y las ediciones desactualizadas de los documentos de estado. Fijan alcance; no autorizan código.

| ID | Decisión | Efecto |
|---|---|---|
| D-069 | **P-015-01** — iPhone con Apple ID gratuito (Personal Team): instalación por cable, perfil de 7 días, sin push APNs ni TestFlight | RF-015-13 opción A: la app en iOS indica que el push no está disponible y HU-05 se comprueba en Android |
| D-070 | **P-015-03** — El rediseño de `vigia-unificado` pasa a ser el diseño vigente de la app, sujeto a revisión visual en Android y iPhone | Sustituye la preservación del diseño móvil de la 010 (D-011-01). T-015-04 |
| D-071 | **P-015-04** — `develop` de este repositorio es la única fuente; `vigia-unificado` queda como antecedente de solo lectura y el trabajo nuevo de su autora entra por ramas `feature/NNN-…` y PR (D-059) | T-015-01 |
| D-072 | **P-015-02** — Sandra compila y prueba iOS en su Mac | Responsable de T-015-08..11 y de la evidencia iOS en `validation.md` |

Autorización: «P-015-02 sandra compila iOS, y autorizo para T-015-01..06. la 07 dejala en pendiente» (sesión del 2026-10-26). Autoriza implementar T-015-01..06 en `feature/015-integracion-unificado`; T-015-07 (Android físico) queda pendiente. No autoriza merge, despliegue ni migración real.

## Respuestas del propietario a la spec 017 — 2026-10-27

Fuente: «estoy de acuerdo con las recomendaciones, sigue con plan.md y tasks.md» (sesión del 2026-10-27), sobre las decisiones pendientes de la [spec 017](../specs/017-robustez-caidas/spec.md).

| ID | Decisión | Efecto |
|---|---|---|
| D-073 | **P-017-01 A** — El estado de monitoreo del nodo (`normal`, `persona_no_visible`, `sin_imagen`, `poca_luz`) viaja como parámetro de la renovación `GET /api/v1/edge/status` y se guarda en `DetectionNode` (último estado y desde cuándo). No es una observación clínica: `risk` y el contrato de 7 claves no cambian | RF-017-09/10. Migración aditiva en `CuidadosApp` |
| D-074 | **P-017-02** — Push genérico, sin prioridad alta y con visibilidad privada para `persona_no_visible` y `sin_imagen`, a los destinatarios de riesgo de la 013 con `risk_alerts` en el plan del titular. `poca_luz` solo se muestra en la app | RF-017-11 |
| D-075 | **P-017-03** — El aviso de nodo sin señal entra en la 017: nodo activo y con permiso que lleva más de 60 s sin renovar, revisado por `send_mobile_reminders` | RF-017-12. La demora real depende de la cadencia del comando (P-012-01, pendiente 14 del estado) |
| D-076 | **P-017-04** — No se incluye la alerta «inmóvil fuera de la cama» de `pose_app`; la caída en línea con la cámara queda como limitación documentada y se reevalúa con el protocolo (D-053) | S-017-03 |
| D-077 | **P-017-05 A** — Titular, familiar y cuidador ven en la ficha del paciente una línea de solo lectura «Cámara: <estado>» con el estado agregado de los nodos activos, sin nombre, id ni última señal del nodo. La tarjeta del nodo y la revocación siguen solo para el titular (`manage_nodes`). Fuente: «para P-017-05 opcion A» (2026-10-27) | RF-017-10, T-017-10 |

Sin autorización de implementación.

## Spec 019 — Migración a FastAPI + Firebase (2026-10-28)

Fuente: revisión del proyecto `vigia 26` de otro integrante del equipo (commit `518792263c44`) y respuestas del propietario en la sesión del 2026-10-28: a la lista inicial («1.B, 2,A, 3.B, 4.A, 5.A, 6.A, 7.C, 8.A, 9.A, 10.B, 12.A, 13.A, 14.A, 15.C, 17.C, 18.A, 19.A, 20.B (portal web a futuro), 21.B 22.A, 24.A»); a las recomendaciones posteriores («concuerdo con tus decisiones»), que cambiaron la 2, la 10 y la 12 y resolvieron la 11, la 16, la 23 y la autenticación del nodo; y a «mantén los recordatorios como respaldo, aunque el servidor sea la fuente principal». D-078..D-080 están en la rama de la 018, sin fusionar. Detalle en la [spec 019](../specs/019-migracion-firebase/spec.md).

| ID | Decisión | Efecto |
|---|---|---|
| D-081 | **1.B + 3.B** — Se migra a FastAPI + Firebase antes de la entrega (unas 3 semanas), de una vez, en `feature/019-migracion-firebase`. `develop` conserva Django como respaldo. Punto de control el 2026-11-04: nodo real → caída → push en Android | Si el punto de control falla, se recomienda entregar con Django. Sustituye la arquitectura Django de `AGENTS.md` solo en la rama hasta la fusión |
| D-082 | **2 (revisada) + 4.A** — El backend FastAPI y la app Flutter del proyecto base son la base del código; se les suman las piezas de este repositorio (Edge, detección, alertas, push, recordatorios, consentimiento). Un solo repositorio y una sola `develop`; `vigia 26` queda como antecedente de solo lectura, como D-071 | Reemplaza la elección inicial 2.A |
| D-083 | **5.A** — `AGENTS.md` y `CLAUDE.md` se actualizan en la rama antes de escribir código | La constitución no cambia: sus principios no mencionan Django |
| D-084 | **6.A + 12.A** — Firestore como base de datos y Firebase en plan Spark, sin cuenta de facturación. Se excluyen Cloud Run, Cloud Scheduler y Cloud Functions | Cuotas diarias de Spark: ver D-095 |
| D-085 | **8.A** — Sin migración de datos: se parte de cero | No se trasladan cuentas ni consentimientos de Django |
| D-086 | **9.A + nodo** — El contrato Edge (`/api/v1/edge/status` y `/api/v1/edge/observations`) no cambia. El nodo se autentica con un token emitido por FastAPI al vincularlo, del que solo se guarda el SHA-256. No se usa una cuenta Firebase por nodo ni la clave de servicio en el nodo | El código del Edge no cambia; solo la URL y el token |
| D-087 | **7.C + 18.A** — Las reglas del backend base se revisan una por una (P-019-02, con valores por defecto en el plan). Se adoptan sus hojas de registro: a tiempo, con retraso y hora real, no dada con motivo, y corrección | Cambia los estados de toma de la 009/010 |
| D-088 | **10 (revisada)** — Recordatorios desde el servidor: cron-job.org llama cada minuto a `POST /internal/tick` con un secreto y el backend envía el push | Reemplaza 10.B (Cloud Scheduler), que exigía facturación |
| D-089 | **Recordatorios de respaldo** — La app conserva los avisos locales programados al sincronizar, con el mismo identificador de toma (`{medId}_{instanteUTC}`), y los cancela al registrar la toma | Los avisos suenan aunque no haya red |
| D-090 | **15.C** — Pagos simulados; el cobro real queda como trabajo futuro | — |
| D-091 | **11.C** — FastAPI en Render, plan gratis, con un solo proceso. El cron de cada minuto lo mantiene despierto; el Edge también, al renovar cada 10 s | Sin SLA: la disponibilidad ≥ 99,5 % queda como límite declarado |
| D-092 | **13.A + 14.A** — Firebase Auth (correo y Google) para personas; portal web en React, mínimo para la HU-07 | Reemplaza allauth y el portal Django en la rama |
| D-093 | **19.A, 20.B, 21.B, 22.A** — La app adopta la paleta, Nunito y los tamaños mínimos del proyecto base (`docs/diseno-visual.md`) junto con la migración; el portal web, más adelante; el ícono se deriva del logo (iOS y Android adaptativo) | Sustituye los colores de `mobile/lib/shared/vigia_design.dart` |
| D-094 | **16.A + 17.C** — App con Riverpod y go_router (viene con la base); barra de 5 secciones: Hoy, Pacientes, Alertas, Posturas y Cuenta | — |
| D-095 | **Supuesto técnico reversible** — Para quedar dentro de la cuota de Spark (50.000 lecturas y 20.000 escrituras al día), el backend guarda en memoria la autorización del nodo hasta 60 s (se invalida al revocar, cambiar el plan o el consentimiento) y escribe la última señal como máximo cada 30 s. La app consulta como máximo cada 5 minutos | Medido en el plan: 1 nodo sin caché ≈ 43.000 lecturas al día |
| D-096 | **23.B** — El informe presenta FastAPI + Firebase como la arquitectura entregada | Hay que volver a validar las HU, RT y RNF; la evidencia Django no se traslada |
| D-097 | **24.A** — Revisar `backend/.env` del proyecto base. Comprobado el 2026-10-28 sin abrirlo: está en `.gitignore` y ningún commit lo incluye, pero sí viaja dentro del zip compartido (`vigia 26 - copia.zip`). Si contiene credenciales reales (no solo los emuladores `demo-*`), su autor debe rotarlas | No se lee ni se copia a este repositorio |

Autorización: «concuerdo con tus decisiones, dejamos develop con django y probamos los cambios en una nueva rama, autorizo que cambies codigo pero antes registra todo» (2026-10-28). Autoriza T-019-01..15. No autoriza merge, despliegue, creación de cuentas ni instalación de software.

### Respuestas del propietario sobre la spec 019 — 2026-10-28

Fuente: «1. autorizo a instalarlos con winget, 2. las privacidad sobre todo, y 3. deja pendiente el crear el proyecto firebase, el servicio en Render y la tarea en cron-job.org. puedes seguir con T-019-04 si lo demas esta listo».

| ID | Decisión | Efecto |
|---|---|---|
| D-098 | **P-019-02, diferencias 4 y 5** — La privacidad de la 014 se porta al nuevo backend: purga diaria con los plazos de D-064, exportación JSON de cuenta y paciente, eliminación del paciente y de la cuenta (D-065), con reautenticación por `auth_time` reciente de Firebase | RF-019-24..27, T-019-16. Las diferencias 1, 2, 3, 6 y 7 quedan con su valor por defecto |
| D-099 | **P-019-01** — Se autoriza instalar en este equipo, con `winget`, el JDK 21 y Node LTS, y `firebase-tools` con npm, para los emuladores | T-019-03. Software de desarrollo local; no se usa en producción |
| D-100 | **P-019-03** — Quedan pendientes el proyecto Firebase real, el servicio en Render y la tarea en cron-job.org | Bloquea T-019-07. El punto de control del 2026-11-04 necesita al menos el proyecto Firebase, porque los emuladores no entregan push a un teléfono |
