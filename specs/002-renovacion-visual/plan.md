# Plan técnico — 002 / Renovación visual

Spec: [spec.md](spec.md). Fecha: 2026-10-02.
Estado: implementado tras autorización explícita del alcance completo el 2026-10-02. Validación detallada en [validation.md](validation.md); revisión visual pendiente y aceptación del propietario pendiente.
Guías aplicadas: 06-cambios, 01-especificar, 02-planificar y 03-tareas; skill [frontend-design](../../.codex/skills/frontend-design/SKILL.md).

## Inspección inicial — antecedente de DOCUMENTAR

- Leídos constitución, README, proyecto/estado, índice, arquitectura, decisiones, observaciones, entorno, trazabilidad y spec 001. Inspeccionados layouts, menú, cabecera, páginas de usuarios/inicio, formularios, permisos, scripts y CSS propios; revisada estructura de cuenta/MFA/errores.
- Solo existe la spec numerada 001; 002 libre. RenovaciónVisual describe un cambio transversal, no una app a registrar. No hay colisión con homeApp, UsuarioApp ni theme; no se ejecutará startapp.
- Esta copia no tiene Git: git status y git branch devuelven «not a git repository». La referencia main en el estado anterior pertenece a la entrega histórica, no a la copia actual. No hay diff fiable contra la base principal. Se preserva todo código existente durante DOCUMENTAR.
- Navegación oscura de 18 rem, fondo global gris oscuro y paneles blancos. Colores directos en HTML, static/css, gráfico y widget de cargo. El CSS de mensajes contiene un selector global button; perfil muestra aria-expanded fijo y enlaces con tabindex=-1; el panel móvil tiene transiciones pero requiere revisión del foco.
- Los botones activar/desactivar del listado comparan RESTRICTED parcialmente; el servidor usa el helper/mixin. La renovación alinea visibilidad, sin modificar su política.
- LOCAL_APPS está realmente en core/common_settings.py; settings.py reutiliza la configuración común. No cambiar registro de apps ni rutas.
- No se levantó servidor ni se inspeccionó interfaz en navegador. No se leyó .env, DB ni media personal. El entorno virtual documentado previamente tenía problemas; su funcionamiento actual no se ha probado.

## Dirección visual propuesta

Sujeto: base reutilizable para personas que gestionan acceso, usuarios y seguridad. Trabajo principal: encontrar acciones y completar formularios con claridad. No se necesita una portada comercial ni un dashboard ficticio.

Propuesta: superficie de trabajo clara, contenido alineado a la izquierda, barra lateral compacta con selección mediante una franja y fondo tenue, cabecera discreta y títulos con acciones al lado. La identidad se concentra en la navegación activa y las acciones principales. El resto utiliza superficies limpias y separación por espacio/bordes; sombras reservadas para elementos flotantes.

### Paleta y tipografía

Valores implementados; contraste medido en [evidencia/contraste.json](evidencia/contraste.json):

| Nombre | Hex | Uso |
|---|---|---|
| Fondo frío | #F2F5F8 | Fondo de trabajo |
| Superficie | #FFFFFF | Navegación, formularios y contenido |
| Tinta | #182536 | Texto principal |
| Texto secundario | #506177 | Ayudas y metadatos |
| Borde | #D9E2EA | Separaciones decorativas; controles usan #758599 para cumplir 3:1 |
| Petróleo | #0F766E | Acción principal, foco y selección |

Texto sobre marca: blanco en las paletas previstas, sujeto a contraste. Alternativas de marca: ciruela #7E22CE y cobre #9A3412. Estados éxito, error, aviso e información tienen tokens separados de la marca y texto/icono propios. Las series del gráfico usan tokens diferenciados, no el color de marca para todo.

Familia propuesta: Segoe UI y pila sans-serif del sistema. Roles: títulos 28–32 px/600, secciones 20 px/600, cuerpo 16 px/400, controles 14–16 px/600 y ayudas 14 px/400; cifras tabulares donde corresponda. Títulos sin mayúsculas forzadas, texto auxiliar con línea de 65–75 caracteres y alturas de línea cómodas. Sin fuente remota ni nueva dependencia.

Espaciado sobre unidad de 4 px; márgenes de página 16/24/32 px según ancho. Navegación de aproximadamente 240 px en escritorio, cabecera 64 px, contenido con ancho máximo cercano a 1280 px. Formularios de una columna de hasta 640 px, con registro a dos columnas solo cuando favorezca su lectura. Radios diferenciados: controles 8 px, paneles 12 px, etiquetas compactas; no todas las secciones se envuelven en tarjetas.

### Composición conceptual

Wireframes documentales; no prototipos funcionales:

```text
Escritorio
+--------------------+---------------------------------------------+
| Identidad          | Título de sección                 Cuenta    |
|                    +---------------------------------------------+
| Inicio             | Título / explicación           Acción       |
| Usuarios           |                                             |
| Registro permitido | Actividad real: últimos accesos              |
|                    | Tabla o estado vacío                         |
| Seguridad          |                                             |
| Perfil             | Demostración del gráfico, claramente rotulada|
| Cerrar sesión      |                                             |
+--------------------+---------------------------------------------+

Móvil
+------------------------------------+
| Abrir menú   Sección      Cuenta    |
+------------------------------------+
| Título y acción en líneas propias  |
| Contenido principal                |
| Tabla con desplazamiento local     |
+------------------------------------+
```

Login: composición asimétrica en escritorio, área de identidad sobria y formulario protagonista; en móvil, una sola columna. Mantener recursos de marca existentes mientras no se aporte otro logo, con textos alternativos neutros y correctos. Usuarios: priorizar nombre/estado y búsqueda; evitar que cada acción requiera una tarjeta decorativa idéntica. Inicio: actividad existente primero, demostración después; no inventar conteos de negocio.

Alternativa considerada: navegación superior única. Se prefiere lateral compacta porque la base será ampliada con módulos y ya tiene una definición compartida de menú. Otra alternativa, conservar composición y cambiar solo acento, no cumple la renovación integral solicitada.

Revisión frente al brief: se descarta trasladar el actual fondo oscuro a una variante con botones nuevos, introducir gradientes/glassmorphism o animar cada tarjeta. La diferenciación se apoya en composición clara, densidad útil y personalización centralizada. La aceptación estética será del propietario; la inspección estática no permite declararla lograda.

## Sistema de colores e integración

Archivos nuevos creados durante la implementación:

- static/css/tokens.css: única fuente editable de color; nombres semánticos de marca, texto sobre marca, marca tenue/hover, superficies, texto, bordes, foco, estados y series. Paletas de ejemplo comentadas y contrato documentado. Las variantes derivadas deben ser consistentes; si una derivación no cumple contraste, usar valor explícito en este mismo archivo.
- static/js/interfaz.js: comportamiento compartido solo si lo exige foco/restauración de scroll/diálogos; inicialización acotada a elementos presentes. Mantener Alpine para estados existentes. No agregar framework de componentes.
- docs/PERSONALIZACION_VISUAL.md: guía de tokens y componentes, creada durante implementación cuando existan las rutas/contratos definitivos.

En base.html cargar tokens antes del CSS compilado y estilos de componentes. En theme/static_src/src/styles.css proponer un puente semántico con @theme inline hacia variables CSS: así las utilidades consumen tokens al renderizar y un cambio de valores no obliga a cambiar clases o recompilar. Las clases nuevas sí requieren build. No ensamblar nombres como bg- + color ni crear un compilador de temas.

CSS propio referencia las mismas variables, con selectores acotados a componentes. Evitar parches globales sobre todos los button/input y cadenas de !important. Para crispy, estilizar dentro del contenedor del formulario, revisando precedencia frente a utilidades de la dependencia. Mantener renderizado/errores de crispy; evaluar override local mínimo solo si el estilo acotado no alcanza. No editar paquetes instalados.

ECharts lee tokens mediante estilos computados una vez disponible el CSS; colores de ejes, leyenda, tooltip, líneas y series se derivan de ese contrato. ResizeObserver ajusta tamaño del contenedor. La inicialización no falla en pantallas sin chart_home. Si no carga el CDN, conservar tabla y una indicación útil del gráfico no disponible. El sistema de marca se prueba recargando tras editar tokens; no se propone selección de tema en vivo.

## Mapa por requisito y archivos reales

Los archivos del mapa fueron intervenidos según su responsabilidad. Se añadieron también `specs/002-renovacion-visual/verificar_js.cjs` (contratos JS mediante Node ya disponible, sin npm ni dependencia del producto) y `verificar_contraste.py` (medición sRGB); resultados y capturas en `evidencia/`.

| RF | Archivos existentes a intervenir | Cambio previsto | Evidencia prevista |
|---|---|---|---|
| 01, 02, 03, 06 | templates/components/Layout/base.html, base_extendido.html, base_pages.html; theme/static_src/src/styles.css; static/css/styles.css | Estructura, tipografía, tokens y responsive, preservar bloques | Capturas comparables y navegador |
| 02, 03, 07 | templates/components/navbar/nav.html, navbar_desktop.html, navbar_mobil.html; templates/components/header/header.html y components/profile.html, buscador.html | Una definición de enlaces, selección, teclado, cabecera | Matriz de actores y panel móvil |
| 02, 04, 06 | templates/components/btn/button.html, button_size.html, ancor_btn.html; paginador.html, input_perfil.html; UsuarioApp/forms.py | Contratos visuales y atributos del widget de cargo; sin cambiar validación | Formularios normales/errores y cambio de paleta |
| 01, 04, 07 | templates/pages/UsuarioApp/usuarios_lista.html, registro_usuario.html, perfil/perfil.html; core/context_processors.py | Nueva composición y visibilidad de gestión mediante regla existente | GET/POST permitidos/denegados, filtros/paginación |
| 01, 04, 06, 07 | templates/account/Layout/base_account.html, base_simple.html; pantallas HTML y snippets de templates/account y templates/mfa | Cuenta, acceso, recuperación y MFA coherentes | Flujos de cuenta con datos ficticios |
| 01, 06 | templates/400.html, 401.html, 403.html, 404.html, 429.html, 500.html | Jerarquía, identidad y acción útil, sin cambiar códigos HTTP | Renderizado aislado de cada plantilla |
| 02, 04, 05, 06 | templates/components/mensajes.html, modal/modal.html, spinner.html, progress.html; static/css/mensajes.css, spiner.css; static/js/mensajes.js, modal.js, script.js | Mensajes/diálogos accesibles, animación acotada, inicialización defensiva | Teclado, ausencia de nodos y movimiento reducido |
| 01, 02, 05, 08 | templates/pages/index.html; static/js/grafico_home.js | Actividad primero, gráfico temático y adaptable | Sin datos/varios tamaños/tema alternativo |
| 07, 08 | UsuarioApp/tests.py, homeApp/tests.py; core/test_settings.py como entorno existente | Regresión significativa; ampliar cobertura de visibilidad y accesos existentes | Suite aislada y revisión de casos |
| 09 | README.md; docs/ARQUITECTURA_BASE.md, DECISIONES.md, TRAZABILIDAD.md, ESTADO_PROYECTO.md; .codex/skills/frontend-design/SKILL.md | Guía y pauta local de reutilización mediante tokens; estado real | Enlaces válidos y prueba guiada de recoloración |

Los layouts de cuenta que extienden base.html directamente requieren revisión individual; no basta modificar base_account/base_simple. theme/templates/base.html es un ejemplo de django-tailwind; no convertirlo en layout de producto sin uso comprobado. CSS generado esperado: theme/static/css/dist/styles.css; nunca editarlo a mano.

## Permisos, datos y contratos

Reutilizar usuario_tiene_cargo y PermitsPositionMixin.permisos. El processor puede exponer puede_gestionar_usuarios con la misma llamada actual, o reutilizar puede_registrar_usuarios si se justifica el nombre; no duplicar listas de cargos. La visibilidad adicional no autoriza modificar reglas de servidor ni consultas. Retener protección de superusuarios y auto-desactivación.

Preservar action/method/CSRF de POST, redirect_field de allauth, multipart de imagen, parámetros search/inactive/page y errores del formulario. Mantener nombres de rutas y bloques head_title, extra_meta, extra_css, javascript, body_class, content, content_main, content_pages y content_account. El logout se presenta con POST/CSRF, sin cierres de sesión por GET.

Sin modelos, relaciones, transacciones nuevas ni migraciones. No cambia semántica de last_activity ni autenticación. Fallos funcionales ajenos encontrados se registran con su reproducción y alcance propio; no se legitiman alterando esta spec.

## Movimiento y accesibilidad

Duraciones orientativas: controles 120–160 ms; paneles/diálogos 180–240 ms; mensajes hasta 200 ms. Animar propiedades concretas. El contenido principal aparece sin cascadas de entradas; una animación no bloquea formulario ni navegación.

Aria-expanded enlazado al estado real, nombres en español, Escape/clic de fondo según componente y retorno de foco. Para desplegable de cuenta preferir una lista de enlaces/botones con Tab normal; conservar role=menu solo si se implementa todo su patrón de teclado. Panel móvil y confirmación modal atrapan foco y hacen inerte el fondo; liberar scroll y foco al cerrar o cambiar a escritorio. x-cloak tiene regla efectiva para evitar parpadeo y controles ocultos no participan en Tab.

Mensajes con región viva apropiada, texto de origen tratado como texto seguro, cierre mediante button y sin selector global que altere otros botones. Conservar mensajes de error del formulario aunque exista notificación temporal. Preferencia de movimiento reducido cubre transiciones Alpine, CSS, scroll suave y opciones de animación ECharts; indicador de carga puede ser estático con etiqueta de estado.

## Plan de pruebas y verificación

Plan original de verificación, no ejecutado en DOCUMENTAR; resultados actuales en validation.md:

1. Revisar entorno antes de ejecutar; usar datos sintéticos y core.test_settings sin .env ni DB real. Preparar servidor de revisión aislado únicamente después de autorización, evitando conectar runserver a db.sqlite3. Si requiere datos de sesión para navegador, usar almacenamiento efímero/local separado conforme al entorno de pruebas, sin cambiar la configuración productiva.
2. python manage.py check --settings=core.test_settings; python manage.py makemigrations --check --dry-run --settings=core.test_settings; python manage.py test UsuarioApp homeApp --settings=core.test_settings. Mantener la suite 001 y ampliar casos de listado/acciones/perfil relevantes. Si se corrige el título «Grafico Ejemplo», actualizar la expectativa literal sin quitar la comprobación de demostración.
3. Comando comprobado: `python manage.py tailwind --settings=core.test_settings build`; el argumento settings va antes de build. Verificar utilidades semánticas, fuentes actuales y exclusión de dependencias/generados. Compilación standalone sin Node/npm.
4. Navegador: login, recuperación, contraseña, cierre público, MFA, Home, búsqueda/listado activos/inactivos, paginación, registro/perfil y confirmaciones. Datos válidos/inválidos, avatar predeterminado y nombres/mensajes largos. Capturar 360/390/768/1024/1440 px, zoom 200 %, teclado y movimiento reducido. Renderizar las seis plantillas de error en entorno aislado; no afirmar que su existencia registra handlers nuevos.
5. Probar matriz de permisos por URL y controles visibles; probar superusuario sin perfil/cargo, RESTRICTED y usuario sin perfil/cargo. Un test de HTML no sustituye el de interacción en navegador.
6. Aplicar tres paletas cambiando únicamente tokens.css. Medir contraste de texto/control/foco y revisar gráfico/formularios/cuenta; revisar CSS computado crispy y errores JS. Comprobar que los cambios de valor no requieren otro build.
7. Registrar resultados reales, capturas, límites y RF en validation.md al validar; no crear una evidencia de ejecución ficticia en esta fase.

## Reversión, riesgos y dependencias

Antes de implementar, preparar copia/snapshot de los archivos concretos a editar, excluyendo secretos, DB y media personal: aquí no hay Git que permita revertir. Recuperar archivos y reconstruir CSS si hay que volver atrás. Sin migración ni pérdida de datos prevista.

Riesgos: precedencia de crispy frente a estilos propios, colores hardcodeados residuales, contratos de scripts/IDs, panel móvil al cambiar viewport, recursos CDN indisponibles y tests literales de textos. Resolver por inspección, estilos acotados y validación; no introducir una actualización masiva de dependencias. «Moderna» no implica solo un nuevo acento ni anima todo.

La paleta es propuesta y la marca comercial está por definir. No se necesita una entrevista de negocio para esta copia. Mantener la skill general y, al actualizarla, añadir únicamente orientación reutilizable del repositorio (tokens/guía/compatibilidad), sin fijar petróleo como elección obligatoria para futuros clientes. Usar skill-creator si se interviene esa skill en la fase posterior.

## Documentos y siguiente fase

Índice, PROYECTO, ESTADO, DECISIONES y TRAZABILIDAD actualizados inicialmente en DOCUMENTAR y nuevamente con la ejecución real. Arquitectura describe ahora los componentes instalados. La [guía de personalización](../../docs/PERSONALIZACION_VISUAL.md) y la orientación local de frontend-design quedaron implementadas; la skill pasó quick_validate.

La instrucción posterior autorizó todas las tareas de esta spec. No hay autorización de despliegue ni aceptación estética/funcional final. T-002-13 permanece parcial por zoom real y preferencia reducida en navegador.

## Ajustes técnicos constatados al implementar

- Navegación móvil y confirmaciones usan `dialog.showModal()` y el script compartido; el fondo inerte y la contención de foco se apoyan en el elemento nativo. Se completa Tab, Escape, scroll y restauración de foco. El desplegable de cuenta mantiene enlaces con Tab normal.
- No fue necesario crear un override de crispy ni editar dependencias: los estilos se acotan a `.form-panel`. Solo se cambiaron atributos visuales en forms.py. `puede_gestionar_usuarios` comparte la llamada al helper con `puede_registrar_usuarios`.
- MFA conserva sus acciones y condiciones; se corrigió composición HTML y slots de presentación, comprobando el flujo TOTP completo en las pruebas del servidor.
- Los recursos propios cambiados usan `?v=002`; el navegador mostró scripts antiguos hasta versionarlos. Cambiar colores no exige build; una publicación posterior debe gestionar la caché según la guía.
- `.venv` no arrancó por su Python inexistente. Se usaron dependencias exactas de requirements.txt en un directorio aislado y el runtime disponible de Codex. No se alteraron requirements, configuración común ni la base real.
- Recuperación en `.recovery-002/antes-implementacion.zip` y manifiesto SHA-256. Revisión efímera en localhost con SQLite en memoria y media temporal; ningún endpoint nuevo del producto.
