# 002 — Renovación visual de Base-2

Estado: implementación del alcance completada; validación visual parcial y aceptación del propietario pendientes. Fecha: 2026-10-02.
Tipo: cambio transversal de presentación; no es una nueva app Django.

Ajuste visual solicitado el 2026-10-05: centrar horizontalmente las tarjetas internas de formulario/cuenta en el espacio disponible junto al menú lateral; conservar ancho, espaciado vertical y alineación interior.
Nombre descriptivo propuesto: RenovaciónVisual. El propietario no pidió un nombre de módulo.
Fuente: renovar totalmente esta copia de la base principal para obtener otra identidad, más moderna, con colores fáciles de cambiar y mejores animaciones/transiciones; usar la skill frontend-design añadida al proyecto.
Implementación autorizada: **sí, alcance completo**, por instrucción explícita del propietario posterior a la revisión documental, el 2026-10-02. La fase inicial se limitó a Markdown según AGENTS.md y D-002. La autorización de código no incluye producción, despliegue, commits ni push. Aceptación estética y funcional: pendiente.

## Problema y resultado

Las plataformas derivadas repiten el mismo diseño. La copia combina fondo y navegación oscuros con formularios blancos, botones índigo y otros colores escritos directamente en plantillas, widgets, notificaciones y gráfico. Cambiar la identidad requiere localizar muchas decisiones dispersas.

Se necesita una segunda base visual reutilizable: renovar composición, jerarquía, navegación, formularios, pantallas de cuenta y estados, conservando las capacidades actuales. El resultado debe diferenciarse en estructura y presentación, además de la paleta. Un responsable técnico debe poder cambiar el color de marca desde un único archivo sin modificar cada pantalla.

El producto sigue siendo una base de gestión de cuentas, acceso y actividad, sin dominio comercial definido. No se inventarán ventas, indicadores de negocio ni módulos para rellenar el diseño.

## Alcance y exclusiones

Incluye estructura compartida de escritorio/móvil, navegación y cabecera, inicio con actividad real y gráfico demostrativo, listado/registro de usuarios, perfil, pantallas HTML de cuenta y MFA existentes, errores 400/401/403/404/429/500, botones, enlaces de acción, formularios crispy, paginación, diálogos, mensajes y carga. Incluye documentación para personalizar colores y reutilizar componentes en futuras apps.

Conserva apps, modelos, contratos de formularios, autenticación allauth/MFA, rutas, permisos del servidor, idioma es-cl y zona America/Santiago. La coherencia de botones visibles con los permisos actuales forma parte de esta renovación.

Quedan fuera nuevos módulos de negocio, reescritura de autenticación, cambio de framework, panel de administración Django, plantillas de correo de texto, cambios de políticas de acceso, datos/esquema, SMTP, actualización de dependencias, selector de colores persistente por usuario, modo oscuro adicional, despliegue, commits y push. Estos últimos dos ajustes visuales podrán proponerse después; no son necesarios para cambiar la identidad por proyecto.

## Actores y permisos por acción

Matriz que conserva las vistas inspeccionadas. «Sí» requiere sesión válida de cuenta activa. Staff por sí solo no concede ADMIN/MANAGER. El acceso público a flujos de cuenta depende de las condiciones vigentes de allauth (token, sesión, MFA), no de un permiso nuevo.

| Acción | Anónimo | ADMIN activo | MANAGER activo | RESTRICTED activo | Activo sin perfil o sin cargo | Superusuario activo, incluso sin perfil/cargo |
|---|---|---|---|---|---|---|
| Inicio y listado de usuarios | No; login | Sí | Sí | Sí | Sí | Sí |
| Ver/editar su propio perfil | No; login | Sí | Sí | Sí | Sí; la vista crea el perfil ausente como hoy | Sí |
| Registro interno GET/POST y su enlace | No | Sí | Sí | No | No | Sí |
| Activar/desactivar cuentas y sus botones | No | Sí | Sí | No | No | Sí |
| Cuenta/contraseña/MFA | Condiciones actuales de allauth | Condiciones actuales de allauth | Ídem | Ídem | Ídem | Ídem |
| Registro público | No | No | No | No | No | No |
| Cambiar identidad de la copia | Fuera de la web: responsable técnico edita tokens del proyecto | Ídem | Ídem | Ídem | Ídem | Ídem |

Las cuentas inactivas no obtienen permisos positivos; los backends pueden tratarlas como anónimas. La desactivación conserva las protecciones actuales contra la propia cuenta y un superusuario. No basta ocultar acciones: el POST sigue protegido por PermitsPositionMixin. No se extiende ese mixin a Home, listado o perfil.

## Historias y flujo

1. Un usuario inicia sesión y reconoce una estructura visual consistente entre Inicio, Usuarios, Perfil y Seguridad. La renovación conserva la dirección solicitada tras el login.
2. Busca usuarios, cambia entre activos/inactivos y pagina; mantiene filtros y entiende qué acción está disponible. «Desactivar» describe la operación real, sin sugerir borrado de datos.
3. Completa un formulario válido o corrige errores; etiquetas, ayuda, foco y mensajes siguen siendo visibles y comprensibles.
4. En móvil abre/cierra navegación o un diálogo, puede recorrerlo con teclado y recupera el foco al cerrar. Las transiciones muestran el cambio de estado.
5. El responsable técnico cambia la paleta de marca en un solo archivo; botones, enlaces, navegación activa, foco y gráfico reflejan la misma identidad tras recargar.

## Requisitos funcionales

- **RF-002-01 — Identidad integral.** Todas las pantallas del alcance adoptan una dirección visual coherente, con nueva jerarquía, composición, tipografía, espaciado y tratamiento de navegación. Inicio separa actividad real de demostración; no incorpora métricas ficticias de negocio.
- **RF-002-02 — Colores centralizados.** Marca, texto sobre marca, superficies, texto, bordes, foco y estados tienen tokens semánticos. La marca y sus variantes se cambian desde un único archivo documentado. No quedan colores de marca duplicados en plantillas, widgets o JS; éxito/error/advertencia conservan su significado independiente de la marca.
- **RF-002-03 — Navegación adaptable.** Se conservan destinos y una sola definición del menú; estado activo perceptible, identidad legible y contenido usable de 360 a 1440 px. En móvil la navegación oculta no recibe foco, Escape cierra, el foco retorna al disparador y el fondo no se recorre mientras el panel modal está abierto.
- **RF-002-04 — Componentes y formularios.** Botones, búsqueda, campos crispy, imagen de perfil, paginación, estados vacíos, errores y confirmaciones comparten reglas visuales. Se conservan nombres/tipos de campos, método, action, CSRF, archivos y validación del servidor. La confirmación de desactivar no envía una acción al abrir/cerrar.
- **RF-002-05 — Movimiento útil.** Transiciones breves responden a apertura/cierre, foco y acciones. Evitar animaciones constantes y cascadas decorativas. Con prefers-reduced-motion se suprime movimiento no esencial, también en scroll, gráfico y carga, conservando información de progreso.
- **RF-002-06 — Accesibilidad y legibilidad.** Navegación por teclado, foco visible, etiquetas asociadas, nombres de controles, estados no comunicados solo por color y contraste mínimo objetivo 4,5:1 para texto normal y 3:1 para texto grande/controles. Zoom al 200 % sin pérdida de acciones; mensajes largos no desbordan. Diálogos gestionan foco y mensajes se anuncian sin robarlo.
- **RF-002-07 — Permisos y regresiones.** Conservar la matriz y flujos existentes. Registro y acciones de gestión visibles usan la misma regla de cargo que el servidor, incluyendo superusuario sin perfil; no comparaciones parciales en plantillas. Mantener cierre público, MFA, edición del perfil, filtros/paginación y logout con POST/CSRF.
- **RF-002-08 — Inicio y gráfico.** Mantener actividad reciente, últimos cinco accesos y aclaración de su carácter aproximado. El gráfico sigue siendo demostrativo, usa colores/fuentes del tema, se adapta al tamaño disponible y respeta movimiento reducido. No exige cambios de datos ni fórmulas.
- **RF-002-09 — Reutilización documentada.** Documentar archivo exacto de tokens, paletas de ejemplo, qué cambia y qué se mantiene semántico, cómo elegir texto de contraste, cuándo recompilar Tailwind y cómo usar los componentes en una nueva pantalla. Comprobar la personalización completa con dos paletas adicionales, sin editar HTML/JS/Python para recolorear. Adaptar la orientación de la skill local para referenciar la guía y favorecer este contrato reutilizable sin fijar una paleta para todos los productos.

## Datos y reglas

Sin datos persistentes nuevos, modelos, migraciones, endpoints ni auditoría adicional. Los tokens son configuración estática del proyecto; no viajan como CSS recibido de un usuario. No se guarda una preferencia en base de datos, cookies o localStorage.

Se conservan User, Profile y Position y sus validaciones actuales, incluido tamaño de imagen de 5 MiB y selección actual de cargos. Las pruebas y capturas utilizarán usuarios/imágenes sintéticos. No se leen .env, db.sqlite3 ni archivos personales para diseñar.

## Criterios de aceptación

| RF | Dado / cuando | Entonces |
|---|---|---|
| RF-002-01 | Comparar antes/después de login, Inicio, Usuarios y Perfil | Cambio claro en composición y jerarquía, misma identidad entre pantallas; revisión visual del propietario pendiente hasta confirmación |
| RF-002-02, 09 | Aplicar marca petróleo, ciruela y cobre usando solo el archivo de tokens | Cambian acciones, enlaces, selección, foco y series de ejemplo; no hay retoques por pantalla; contraste comprobado para cada paleta |
| RF-002-03, 06 | Navegar a 360/390/768/1024/1440 px y con zoom 200 % | Sin recortes ni scroll horizontal de página; una tabla puede tener scroll local anunciado; panel móvil y foco funcionan |
| RF-002-04 | Enviar formularios válidos e inválidos y seleccionar imagen sintética | Se mantienen validación y guardado; errores/ayudas legibles; no desaparecen campos ni CSRF |
| RF-002-04, 05, 06 | Abrir/cancelar/confirmar diálogo y cerrar un mensaje con teclado | Acción explícita, foco controlado, Escape/cancelación sin escritura; mensajes largos caben y cierre accesible |
| RF-002-05 | Repetir interacciones con movimiento reducido | Sin desplazamientos/escala/animación no esenciales ni scroll suave; contenido/estado de carga siguen disponibles |
| RF-002-07 | Cada actor de la matriz usa menú y solicita GET/POST directamente | Visibilidad y respuesta coherentes, sin elevar privilegios; superusuario sin perfil conserva acceso de gestión |
| RF-002-08 | Inicio con actividad/ausencia de accesos y redimensionar el gráfico | Tabla real y demostración distinguidas, estados vacíos útiles, gráfico sin desbordar ni aparentar datos reales |
| RF-002-09 | Otro desarrollador sigue la guía de personalización | Localiza un único archivo de colores y usa componentes existentes sin repetir la paleta |

## Compatibilidad y calidad

Mantener Django Templates, CBV, crispy_tailwind y Tailwind 4 standalone. No añadir dependencias de UI, paquetes npm, fuente remota ni biblioteca de animación por rutina. Reutilizar Alpine y ECharts existentes. Objetivo: animar opacity/transform y propiedades visuales concretas, evitando transition: all y desplazamientos por carga de fuente.

La spec 001 conserva su alcance histórico y evidencia; la 002 implementa una evolución de presentación, manteniendo sus controles y pruebas funcionales. Se adaptó la expectativa del título del gráfico conservando la comprobación de demostración.

## Supuestos y decisiones pendientes

- Dirección propuesta: espacio de gestión claro, navegación compacta y acento petróleo; alternativas cromáticas ciruela y cobre. Son propuestas reversibles, no preferencias ya aprobadas.
- Tipografía propuesta: pila del sistema con Segoe UI preferida para esta base Windows; sin nueva descarga. Marca comercial/logo finales por definir; no se inventa empresa ni se convierte el logo existente en un sistema de logotipos nuevos.
- «Fácil cambiar colores» se concreta por archivo de configuración estática y guía; un editor de colores dentro de la web requeriría alcance posterior.
- No apareció una decisión crítica de negocio ni migración nueva durante la implementación. La autorización posterior ya fue recibida; la aceptación visual final sigue pendiente. Zoom real al 200 % y movimiento reducido activado en navegador quedan pendientes de verificación, sin alterar estos criterios.

## Revisión y cambios

2026-10-02: primera propuesta de renovación de esta copia. Inspección estática y documentos; sin código, build, pruebas de aplicación ni navegador. Ver [plan](plan.md) y [tareas](tasks.md).

2026-10-02, instrucción posterior: revisión documental y autorización explícita del alcance completo. Implementación, 27 pruebas Django, cinco comprobaciones JS, build, check, detección de migraciones y navegador sobre datos sintéticos. Evidencia y límites en [validation.md](validation.md). Los RF y criterios de aceptación se conservan.
