# Arquitectura de la base recibida

Referencia: core-base.zip, 2026-09-20. Describe lo observado; no certifica funcionalidades no probadas.

## Componentes

| Área                     | Archivos existentes                                                                                                                                                                                 | Responsabilidad                                           |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| Configuración            | [common_settings.py](../web/core/common_settings.py), [settings.py](../web/core/settings.py), [test_settings.py](../web/core/test_settings.py)                                                                  | Base común sin entorno; entrada normal y pruebas aisladas |
| Rutas raíz               | [urls.py](../web/core/urls.py)                                                                                                                                                                          | admin, allauth, homeApp y UsuarioApp                      |
| Permisos por cargo       | [mixins.py](../web/core/mixins.py)                                                                                                                                                                      | usuario_tiene_cargo y PermitsPositionMixin                |
| Usuarios/perfiles/cargos | [models.py](../web/UsuarioApp/models.py), [views.py](../web/UsuarioApp/views.py), [forms.py](../web/UsuarioApp/forms.py)                                                                                        | Gestión de cuentas y perfiles                             |
| Inicio y actividad       | [views.py](../web/homeApp/views.py), [middleware.py](../web/homeApp/middleware.py)                                                                                                                          | Cinco accesos recientes y actividad aproximada            |
| Presentación             | [base.html](../web/templates/components/Layout/base.html), [base_extendido.html](../web/templates/components/Layout/base_extendido.html), [base_pages.html](../web/templates/components/Layout/base_pages.html) | Estructura y bloques compartidos                          |
| Menú                     | [nav.html](../web/templates/components/navbar/nav.html), [context_processors.py](../web/core/context_processors.py)                                                                                         | Enlaces y autorización compartida con el servidor         |
| Tema                     | [styles.css](../web/theme/static_src/src/styles.css), [CSS generado](../web/theme/static/css/dist/styles.css)                                                                                                | Tailwind 4 standalone, fuentes y compilación              |
| Imágenes de perfil       | [customer_img.py](../web/utils/customer_img.py)                                                                                                                                                         | Redimensionado y recorte                                  |

## Identidad y permisos reales

Se usa User de Django. Profile lo relaciona mediante user_FK, con acceso inverso user.profile. El cargo se obtiene por profile.position_FK.permission_code; Position ofrece ADMIN, MANAGER y RESTRICTED.

La función usuario_tiene_cargo comprueba autenticación y actividad, luego permite superusuario; para otros usuarios compara el cargo contra la lista recibida. No interpreta is_staff como un cargo.

El context processor `permisos_navegacion` conserva esa función y `PermitsPositionMixin.permisos` para `puede_gestionar_usuarios`. Desde 006, `puede_registrar_usuarios` usa `cargos_asignables` y Registro usa `UserRegistrationMixin`, con cargo requerido incluso al superusuario. El menú y los controles no sustituyen el control de la vista; ambos se prueban con la matriz propia de cada acción.

PermitsPositionMixin usa por defecto ADMIN/MANAGER y su atributo existente se llama permisos. Un anónimo se envía al login; un autenticado sin permiso se redirige a Home. Home, listado de usuarios y perfil usan LoginRequiredMixin, no todos el mixin por cargo.

Un módulo nuevo debe especificar lectura/escritura por acción y decidir cómo conserva la excepción de superusuario. No heredar una tabla de permisos de un negocio distinto. Si requiere objetos privados por propietario, definir también ese filtro: el cargo por sí solo no expresa propiedad del dato.

## Presentación

- base.html: estructura general; bloques head_title, extra_meta, extra_css, javascript, body_class y content.
- base_extendido.html: estructura privada con navegación; bloque content_main.
- base_pages.html: extiende la anterior y ofrece content_pages.
- Para una vista pública evaluar base.html sin navegación interna y definir expresamente datos visibles.
- Reutilizar componentes y estilos Tailwind. La adaptación móvil y los permisos de una nueva pantalla necesitan comprobarse, no se garantizan por heredar la plantilla.

El gráfico del inicio usa datos de ejemplo. La tabla de accesos consulta usuarios reales; «actividad reciente» es una aproximación temporal, no prueba de conexión abierta.

## Datos y fronteras

- `UsuarioApp.Profile.position_FK.permission_code` es la fuente actual de permisos.
- <Añadir mas segun se integran mas modulos o funciones>

## Configuración y pruebas

`core/common_settings.py` contiene valores compartidos sin leer `.env`. `core/settings.py` sigue siendo la entrada normal y carga el entorno; `core/test_settings.py` no la importa y define SQLite en memoria, correo/caché locales, hasher rápido y rutas temporales. Las pruebas deben indicar `--settings=core.test_settings`.

Tailwind 4 se compila con el binario standalone administrado por django-tailwind; no usa Node.js, `package.json` ni `tailwind.config.js`. `theme/static_src/src/styles.css` desactiva la detección automática y registra raíces HTML, JavaScript y Python propias mediante `@source`; excluye migraciones, cachés y `staticfiles`. Las clases construidas por concatenación no son detectables de forma segura: escribir nombres completos o usar `@source inline()` de forma finita.

## Extender mediante un módulo

Durante DOCUMENTAR solo proponer:

1. Si corresponde una nueva app Django o ampliar una existente.
2. Nombre y responsabilidad, modelos/relaciones y contratos de entrada/salida.
3. Registro en LOCAL_APPS y ruta include cuando sea una nueva app.
4. Namespace/rutas que eviten colisiones y plantillas/estáticos organizados por módulo.
5. Permisos, validación, comportamiento ante errores e integración con el menú.
6. Pruebas, cambios de esquema y estrategia de reversión si aplica.

Solo después de autorizar código se crean esos archivos. No renombrar core, UsuarioApp, homeApp ni tablas compartidas para personalizar la marca del cliente. El nombre comercial se registra en PROYECTO.md y en la interfaz cuando esa tarea esté autorizada.

## Qué no impone la base documental

No exige una política universal de auditoría ni una app por pantalla. Esas son decisiones de cada spec. Tampoco agrega un sistema de servicios, tareas asíncronas, API o nuevo motor de datos sin necesidad.

## Sistema visual implementado — spec 002

La [spec 002](../specs/002-renovacion-visual/spec.md) renueva presentación sobre los layouts, bloques, apps y menú existentes. [tokens.css](../web/static/css/tokens.css) es la fuente de colores; el puente `@theme inline` conecta utilidades semánticas de Tailwind. El CSS propio, widget de cargo y gráfico consumen ese contrato. Valores de color no requieren recompilar; nuevas clases/fuentes sí. La [guía](PERSONALIZACION_VISUAL.md) describe componentes y caché.

El [script compartido](../web/static/js/interfaz.js) gestiona diálogos nativos, foco, scroll y desplegable de cuenta; las notificaciones se renderizan una sola vez y tratan contenido como texto. Login usa layout público; cuenta interna/MFA reutiliza navegación privada. CSS y gráfico contemplan movimiento reducido.

No cambió modelos ni rutas. LOCAL_APPS permanece en core/common_settings.py y settings.py lo reutiliza. La skill local referencia la guía sin fijar una paleta para futuros productos. Validación y límites en [validation.md](../specs/002-renovacion-visual/validation.md).

## Modo visual por cuenta — implementado en 003

El [plan 003](../specs/003-modo-visual-usuario/plan.md) se implementó en UsuarioApp con UserVisualPreference uno a uno con el usuario, sin nueva app ni cambios a Profile. `/preferencias/modo-visual/` (VisualModeUpdateView) guarda por POST/CSRF solo la cuenta activa de la sesión, cualquiera sea el cargo; form ChoiceField light/dark y unique/check de base. Processor `preferencias_visuales` registrado en common_settings consulta la fila propia sin crearla; renderiza data-mode antes del CSS. Inicio envía el destino explícito y vuelve por redirect; no requiere scripts/localStorage ni altera permisos de otras vistas.

Tokens contienen pares de marca clara/oscura, variantes semánticas y color-scheme; QR mantiene superficie blanca. El gráfico existente consume los valores al recargar. Valores inválidos/fallo previsto de escritura usan 400/500 contextual; fallo de lectura de esta preferencia usa claro, sin certificar recuperación de toda la DB. [Validación](../specs/003-modo-visual-usuario/validation.md).

Migración 0002 creada y probada/revertida únicamente en SQLite efímero, sin backfill. Aplicar o revertir esquema sobre la base existente requiere autorización propia del entorno/respaldo; rollback pierde preferencias. Código entregado no significa tabla instalada en datos reales.

## Gestión por destinatario — implementada en 004

[Spec 004](../specs/004-administracion-usuarios/spec.md) amplía UsuarioApp con [permissions.py](../web/UsuarioApp/permissions.py): política por acción/actor/destinatario compartida por vistas y flags de fila. ADMIN gestiona inferiores y MANAGER solo RESTRICTED al activar/desactivar. Incluso superusuario requiere cargo, sin excepción en estas acciones. AccountManagementMixin acotado aplica política con actor vigente; usuario_tiene_cargo/PermitsPositionMixin y el processor global/Registro conservan su contrato.

AdministrativePasswordForm reutiliza SetPasswordForm con reconfirmación del operador, ruta privada UserPasswordReset y plantilla sobre base_pages/content_pages. Escrituras mínimas password/is_active, CSRF, transacciones, validadores/hashing/sesiones Django; no actualiza Profile/MFA/modo visual ni correo. never_cache/campos sensibles y errores previstos con contexto en 500.html. UserActivateView comparte vista de estado con UserDeactivateView. Sin nueva app/modelos/migraciones/SMTP ni importaciones del proyecto de referencia. [Validación](../specs/004-administracion-usuarios/validation.md): 57 tests, 60 plantillas, check/build y navegador parcial; SQLite no certifica bloqueos PostgreSQL.

## Registro e integridad actuales — specs 005/006

El contrato de Registro de 001 queda sustituido por 006. UserRegistrationMixin y cargos_asignables en UsuarioApp/permissions.py protegen Registro y el flag puede_registrar_usuarios; ProfileCreateForm recibe actor y filtra por permission_code. ADMIN solo inferiores, MANAGER RESTRICTED y únicamente root con ADMIN asigna ADMIN; nadie sin cargo obtiene excepción. Se conserva core.mixins y puede_gestionar_usuarios para sus otros consumidores, además de la política independiente 004.

Alta/edición User/Profile usan atomic; Profile.save prepara fotos nuevas en memoria, escribe storage y DB, compensa fallos y elimina anterior con on_commit. Cambios sin foto no la procesan. No cambió esquema. Se probó almacenamiento local; limpieza fallida exige mantenimiento del producto.

005 actualiza Django/allauth y rutas/settings MFA equivalentes; extra MFA instalado con TOTP/recuperación explícitos, sin WebAuthn/socialaccount. Lock con hashes y preflight de actualización allauth de solo lectura. Ver [DEPENDENCIAS.md](DEPENDENCIAS.md) y validaciones 005/006 para comandos/limitaciones. Opcionales axes/concurrentlogins siguen comentados, settings normal intacto.

## Extensión implementada 007 — PlanesApp

Namespace PlanesApp bajo /planes/, LOCAL_APPS en core/common_settings.py y socialaccount/Google registrados. Plan/PlanBenefit, Subscription única por User, métodos ficticios y SimulatedOperation con snapshots/idempotencia; 0001 esquema y 0002 seed/cargo, ensayadas sin DB real. [Código](../web/PlanesApp/services.py), [plan](../specs/007-planes-app/plan.md), [validación](../specs/007-planes-app/validation.md).

UsuarioApp incorpora servicio de alta/adapters y SignupForm transaccional para User/Profile RESTRICTED/Free/EmailAddress. Google conserva cargos al reingresar; email coincidente no autentica/fusiona y exige conexión desde sesión existente. Credenciales APP por entorno; sin tokens persistidos, POST/CSRF/PKCE. Verificación optional mantiene login/MFA internos; ClientMixin/servicios requieren EmailAddress verificado para métodos/compra/renovación.

Home redirige clientes antes de consultar usuarios; UserListView exige helper ADMIN/MANAGER/root. Objetos cliente siempre filtrados por titular, incluso root. Registro/gestión 004/006 conservados. Servicios ejecutan operaciones atómicas con precios del servidor, propuestas firmadas/versiones, bloqueos y nonce único. Tarjetas de lista cerrada, solo máscara/fixture persistidos. Vencimiento se calcula al leer; renovación mediante POST sin scheduler.

Templates integrados en layouts/tokens/menú actuales; CSS/JS de app y @source explícita. Tarjeta única gira al CVC, foco/errores y fallback del formulario sin scripts. [Guía para instalar/configurar](PLANESAPP_DESARROLLO.md). Migración de DB existente/OAuth real/aceptación pendientes; no inferir despliegue por suite verde.

## Evolución propuesta 008 — todavía sin implementar

[Plan 008](../specs/008-dashboard-navegacion/plan.md): ampliar Home existente con agregados lectores de suscripciones, planes y operaciones simuladas. Servicio propuesto PlanesApp/dashboard.py, sin app/modelos/rutas/migraciones nuevas; guard general ADMIN/MANAGER/root activo antes de consultas. Resumen global agregado no concede acceso a métodos/historial ajenos. Población, estados efectivos y volumen mensual especificados; GET no crea filas ni procesa vencimientos por escritura.

Menú compartido propuesto con seis SVG y flag vigente para Inicio; componente de selector visual propuesto para index/Mi suscripción con mismos SVG y POST/CSRF actuales. Gráfico de planes con alternativa HTML sustituiría series meteorológicas. Tokens/layouts y permisos 004/006 permanecen. Es propuesta documental: autorización posterior y pruebas de 008 pendientes.

## Ejecución posterior 008 — implementada

La sección propuesta anterior conserva el antecedente documental. Tras autorización explícita, Home invoca [PlanesApp/dashboard.py](../web/PlanesApp/dashboard.py) después de su guard vigente: cuatro consultas ORM, counts/agrupación por plan efectivo y suma de snapshots monetarios aprobados desde el inicio del mes local. No cambios de esquema ni escrituras de negocio durante GET; el middleware de actividad anterior conserva su contrato.

[Componente visual_mode](../web/templates/components/visual_mode.html) usado en Home/Mi suscripción; nav.html usa el flag interno para Inicio y seis SVG decorativos. Index proporciona datos con json_script y cantidades HTML, grafico_home.js consume estos datos y degrada si no hay ECharts. Base extendida contiene details/noscript con el mismo menú para móvil; CSS permite desplazamiento del sidebar y conserva tokens. Pruebas nuevas agrupadas en [test_dashboard.py](../web/homeApp/test_dashboard.py). [Evidencia y límites](../specs/008-dashboard-navegacion/validation.md): 127 tests, 77 HTML y navegador; aceptación manual pendiente.

## Antecedente de propuesta 009 — previo a autorización

[Plan 009](../specs/009-cuidados-cuidadores/plan.md): una app de cuidados propia por User, registrada después de autorización en LOCAL_APPS real de core/common_settings.py y core/urls.py. Pacientes, medicamentos/horarios, tareas, guías, eventos con snapshots, reloj persistente y acuses. No reconstruye usuarios/auth/tema. Propiedad sin excepción por cargo o root, distinta del helper global interno que conserva su contrato. Sin admin global de modelos sensibles.

PlanesApp incorporaría capacidad 1/3/null y tres planes activos, conservando snapshots/períodos históricos y code pro para nombre Premium. Cuota y operaciones comerciales comparten bloqueo de User; selección versionada de pacientes al reducir cupo, archivo atómico tras éxito y al final de cancelación. Elegibilidad temporal deriva selección efectiva sin escrituras de negocio en GET; materialización por POST explícito. Cancelación conserva derechos hasta cierre, vencimiento sin elección exige resolverla sin selección automática.

Agenda privada derivada de horarios Santiago, ocurrencias identificables y acciones explícitas; posición manual inicia timer 60/90/120 minutos. Poll privado y acuse POST deduplicado mientras web abierta, servidor gobierna tiempos. Sin Celery/push/cámaras/IA ni acceso a pacientes ajenos para operadores. Home de cliente iría a Cuidados, Home comercial interno se conserva; componentes/layouts/modo visual compartidos. Solo propuesta documental; migraciones/tests/assets/rutas todavía no creados.


## Implementación posterior 009 — CuidadosApp

Corrección de selectores 2026-10-06: [override crispy](../web/templates/tailwind/layout/select.html) usa contratos del paquete para attrs/opciones/grupos/múltiples y clases semánticas propias en styles.css. Flecha decorativa pequeña posicionada dentro del campo, independiente de utilidades de site-packages; color del tema y revisión de caché compartidos. [Validación](../specs/009-cuidados-cuidadores/validation.md).

Ajuste visual posterior del 2026-10-06: propiedad CareGuide.illustration selecciona PNG v2/alt solo para las cuatro rutas SVG iniciales; rutas personalizadas conservadas. guide.html compartido en biblioteca/panel/ficha usa revisión de caché independiente de la referencia clínica, carga diferida y HTML educativo existente. Sin campo/migración ni cambio de cuidados. [Evidencia](../specs/009-cuidados-cuidadores/validation.md).

[CuidadosApp/models.py](../web/CuidadosApp/models.py): Patient propio, Medication/MedicationTime, CareTask, CareGuide, CareEvent histórico, PostureTimer, ReminderReceipt y CapacitySelection. Sin Django Admin de modelos sensibles; PROTECT sobre titular/fichas/eventos. [permissions.py](../web/CuidadosApp/permissions.py) exige autenticación/actividad y queries de titular incluso root; no cambia el helper interno.

[capacity.py](../web/CuidadosApp/capacity.py) resuelve cupos/selección por fecha, archive/materialización POST y reducción comercial. [services.py](../web/CuidadosApp/services.py) comparte bloqueo User con PlanesApp, valida tokens/versiones/propiedad y guarda acciones atómicas. [scheduling.py](../web/CuidadosApp/scheduling.py) deriva agenda y avisos sin escribir por GET; claves lógicas únicas, acciones firmadas/versionadas, DST Santiago, schedule_effective_at evita atrasos inventados de edición/reactivación. Correcciones vinculadas conservan historial y alarma.

[CuidadosApp/urls.py](../web/CuidadosApp/urls.py), 21 rutas bajo /cuidados/, registradas en core/urls.py y LOCAL_APPS en common_settings. Home cliente redirige antes de consultas; interno conserva dashboard comercial sin datos clínicos globales. Base autenticada carga care.css/care.js y bandeja de avisos privada; polling 30 s, tiempo servidor/contador monotónico, claim único POST, no storage clínico. Formularios/guías/agenda HTML independientes de scripts.

PlanesApp Plan añade cupo y backup del catálogo; 0003/0004 conservan códigos/FK, Hogar histórico y snapshots comerciales. CuidadosApp 0001 depende de PlanesApp 0004, 0002 guías, 0003 schedule_effective_at. Planes/checkout/cancelación/retiro del último método usan selección propia firmada y archivo tras éxito. @source nuevo y SVG/nav/modo semánticos de la base. [Pruebas](../web/CuidadosApp/tests.py) y [validación](../specs/009-cuidados-cuidadores/validation.md): migraciones solo en memoria, sin dependencias nuevas ni IA/cámaras operativas.


## Propuesta 010 — cliente móvil, todavía sin implementar

[Plan 010](../specs/010-aplicacion-movil/plan.md): Flutter iOS/Android separado en mobile/ (directorio previsto), API versionada propuesta en Django y adaptadores dentro de UsuarioApp/CuidadosApp/PlanesApp. Reutilizar servicios, datos, cuentas, cupos y portal; no existe aún esta API móvil por documentarla. Autenticación compatible con allauth/MFA/Google por definir; ninguna nueva dependencia elegida. Detección MediaPipe incluida por pedido humano; nodo local propuesto y clasificación propia pendientes de definición técnica. Capacidades comerciales en servidor según plan; matriz de funciones nuevas y colaboración pendientes. La arquitectura React/NoSQL/microservicios del informe es referencia divergente, no estado implementado ni autorización de migración.


## Aplicación móvil — actualización 2026-10-19

010 implementa /_allauth/app/v1/ y /api/v1/ para Flutter en mobile/. API adapta services/forms de CuidadosApp y entitlements de PlanesApp. mobile_models agrega nodo, observación, dispositivo y recibo push mediante migración0004; Edge local en edge/ no sube imágenes. Demo aislada en core.mobile_demo_settings. Ver [contrato](../specs/010-aplicacion-movil/contrato.md) y [guía](MOVIL_DESARROLLO.md).

## Arquitectura propuesta011 — no implementada

Separación web/ (Django + API compartida), mobile/ (Flutter por función) y edge/ (nodo MediaPipe). Docs/specs comunes. No segundo servidor de identidad ni DB duplicada; rutas públicas y app labels preservados. [Plan de traslado y límites](../specs/011-ecosistema-instalable/plan.md).
